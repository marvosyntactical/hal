from typing import Union, Optional
from pathlib import Path
import sys
import os

from matplotlib import pyplot as plt

import torch
import torch.nn as nn
import torchaudio
import pytorch_lightning as pl
from pytorch_lightning.callbacks import QuantizationAwareTraining
from dataset import HAL_KW_DATASET

DATASET_PATH = "hal_keywords"
BACKEND = "qnnpack"


"""
This file is entirely based on/copied from the following amazing blog post by
Thomas Viemann:
    https://devblog.pytorchlightning.ai/applying-quantization-to-mobile-speech-recognition-models-with-pytorch-lightning-5be90420453c
specifically its accompanying Notebook:
    https://gist.github.com/t-vi/97dc9d58f0bfae7dcce2afc2307e65df
"""

class HAL_KW(pl.LightningDataModule):
    def __init__(
        self,
        dl_path: Union[str, Path] = "data",
        device: Union[torch.device, str, None] = None,
        num_workers: Optional[int] = None,
        pin_memory: Optional[bool] = None,
        batch_size: int = 128,
        sample_rate = 8000,

    ):
        super().__init__()

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif isinstance(device, torch.device):
            self.device = device
        else:
            self.device = torch.device(device)

        self._dl_path = dl_path
        self._batch_size = batch_size

        if pin_memory is not None:
            self._pin_memory = pin_memory
        else:
            self._pin_memory = (self.device.type == "cuda")

        if num_workers is not None:
            self._num_workers = num_workers
        else:
            self._num_workers = 16 if self.device.type == "cuda" else 0
        self._train_dataset = None
        self._val_dataset = None
        self._labels = None
        self._label_to_index = None
        self.sample_rate = sample_rate
        self._transform = None
        self._input_sample_rate = None

    @staticmethod
    def pad_sequence(batch):
        # Make all tensor in a batch the same length by padding with zeros
        batch = [item.t() for item in batch]
        batch = torch.nn.utils.rnn.pad_sequence(batch, batch_first=True, padding_value=0.)
        return batch.permute(0, 2, 1)

    def transform(self, input, input_sample_rate=None):
        if input_sample_rate is None:
            if self._input_sample_rate is None:
                _, self._input_sample_rate, *_ = self.train_dataset[0]
            input_sample_rate = self._input_sample_rate
        # in TorchAudio master (0.9) there is a functional.resample
        return torchaudio.transforms.Resample(orig_freq=input_sample_rate, new_freq=self.sample_rate)(input)

    def collate_fn(self, batch):

        # A data tuple has the form:
        # waveform, sample_rate, label, speaker_id, utterance_number

        tensors, targets = [], []

        # Gather in lists, and encode labels as indices
        for waveform, input_sample_rate, label, *_ in batch:

            tensors += [self.transform(waveform, input_sample_rate)]
            targets += [self.label_to_index(label)]

        # Group the list of tensors into a batched tensor
        tensors = self.pad_sequence(tensors)
        targets = torch.stack(targets)
        self._label_to_index = None

        return tensors, targets

    def prepare_data(self, download=False):
        """Download waveforms and prepare dataset."""
        os.makedirs(self._dl_path, exist_ok=True)
        # we don't use the dataset, but download here
        # torchaudio.datasets.speechcommands.SPEECHCOMMANDS(root=self._dl_path, download=download)

    @property
    def data_path(self):
        return Path(self._dl_path).joinpath(DATASET_PATH)

    def __dataset(self, train: bool):
        return HAL_KW_DATASET(root=self._dl_path,
            subset="training" if train else "validation")

    @property
    def labels(self):
        if self._labels is None:
            self._labels = sorted({os.path.basename(os.path.dirname(p)) for p in self.train_dataset._walker})
        return self._labels

    @property
    def train_dataset(self):
        # note that we don't do any augmentation (randomness) here, so caching is OK
        if self._train_dataset is None:
            self._train_dataset = self.__dataset(train=True)
        return self._train_dataset

    @property
    def val_dataset(self):
        if self._val_dataset is None:
            self._val_dataset = self.__dataset(train=False)
        return self._train_dataset

    def __dataloader(self, train: bool):
        """Train/validation loaders."""
        return torch.utils.data.DataLoader(
            self.train_dataset if train else self.val_dataset,
            batch_size=self._batch_size,
            shuffle=train,
            drop_last=train,
            collate_fn=self.collate_fn,
            pin_memory=self._pin_memory,
            num_workers=self._num_workers,
        )

    def train_dataloader(self):
        return self.__dataloader(train=True)

    def val_dataloader(self):
        return self.__dataloader(train=False)

    def label_to_index(self, word):
        if self._label_to_index is None:
            self._label_to_index = {l: torch.tensor(idx) for idx, l in enumerate(self.labels)}
        # Return the position of the word in labels, slow...
        return self._label_to_index[word]

    def index_to_label(self, index):
        # Return the word corresponding to the index in labels
        # This is the inverse of label_to_index
        return self.labels[index]

class M5_2d(torch.nn.Sequential):
    def __init__(self, n_input=2, n_output=10, stride=16, n_channel=32):
        super().__init__(
            torch.nn.Unflatten(1, (1, 2)),
            torch.nn.Conv2d(n_input, n_channel, kernel_size=(1, 80), stride=(1, stride)),
            torch.nn.BatchNorm2d(n_channel),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d((1, 4)),
            torch.nn.Conv2d(n_channel, n_channel, kernel_size=(1, 3)),
            torch.nn.BatchNorm2d(n_channel),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d((1, 4)),
            torch.nn.Conv2d(n_channel, 2 * n_channel, kernel_size=(1, 3)),
            torch.nn.BatchNorm2d(2 * n_channel),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d((1, 4)),
            torch.nn.Conv2d(2 * n_channel, 2 * n_channel, kernel_size=(1, 3)),
            torch.nn.BatchNorm2d(2 * n_channel),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d((1, 4)),
            torch.nn.AdaptiveAvgPool2d(1),
            torch.nn.Flatten(),
            torch.nn.Linear(2 * n_channel, n_output),
        )

class KeywordModel(pl.LightningModule):
    def __init__(
            self,
            model_class: nn.Module=M5_2d,
            dm: pl.LightningDataModule=HAL_KW(),
            model=None,
            model_path: str= None
        ):
        # n_input = 1 for mono, 2 for stereo
        super().__init__()
        if model is not None:
            self.model = model
        else:
            self.model = model_class(n_input=1, n_output=len(dm.labels))
            if model_path is not None:
                print(f"Attempting to load weights from {model_path}...")
                try:
                    model.load_state_dict(torch.load(model_path))
                except FileNotFoundError as FNFE:
                    print("Got FileNotFoundError: {FNFE}")
        self.val_accuracy = pl.metrics.Accuracy()
        self.sample_rate = dm.sample_rate

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        inp, label = batch
        pred = self(inp)
        loss = torch.nn.functional.cross_entropy(pred, label)
        # Logging to TensorBoard by default
        self.log('train_loss', loss)
        return loss

    def validation_step(self, batch, batch_idx):
        inp, label = batch
        pred = self(inp)
        loss = torch.nn.functional.cross_entropy(pred, label)
        acc = self.val_accuracy(pred.softmax(dim=-1), label)
        self.log('valid_acc', acc, on_step=True, on_epoch=True)
        self.log('valid_loss',loss, on_step=True, on_epoch=True)
        return loss

    def configure_optimizers(self):
        opt = torch.optim.Adam(self.model.parameters(), lr=0.005, weight_decay=0.0001)
        sched = torch.optim.lr_scheduler.StepLR(opt, step_size=20, gamma=0.1)
        return [opt], [sched]



def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_gpus = 1 if torch.cuda.is_available() else 0
    print(device)
    models = "models/"

    # DATASET PREPARATION
    dm = HAL_KW(dl_path='data', num_workers=4)
    dm.prepare_data(download=True)

    # VISUALIZATION
    waveform, sample_rate, label, utterance_number = dm.train_dataset[0]
    # print("Shape of waveform: {}".format(waveform.size()))
    # print("Sample rate of waveform: {}".format(sample_rate))
    # plt.plot(waveform.t().numpy())

    # FP32 MODEL INITIALIZATION
    # (use 2d architecture here already)
    model = KeywordModel(dm=dm)

    # FP32 TRAINING
    trainer = pl.Trainer(gpus=n_gpus, max_epochs=2, check_val_every_n_epoch=1)  # for real training, I use 40 epochs or so
    trainer.fit(model, datamodule=dm)
    print(model.val_accuracy.compute().item())
    torch.jit.save(model.to_torchscript(), models+'audio_model_fp32.pt')

    # QUANTIZATION PREPARATIONS
    layers_to_fuse = []
    for i in range(len(model.model) - 2):
        if (isinstance(model.model[i], torch.nn.Conv2d) and
            isinstance(model.model[i + 1], torch.nn.BatchNorm2d) and
            isinstance(model.model[i + 2], torch.nn.ReLU)):
            layers_to_fuse.append([f'model.{ii}' for ii in [i, i + 1, i + 2]])
    print(layers_to_fuse)

    # QAT
    qmodel = KeywordModel(dm=dm)
    # for real training, t-vi uses 40 epochs or so instead of just 2
    qtrainer = pl.Trainer(gpus=n_gpus, max_epochs=1, check_val_every_n_epoch=1, callbacks=[
        QuantizationAwareTraining(qconfig=BACKEND, modules_to_fuse=layers_to_fuse)])
    print("Fitting quantization aware model")
    qtrainer.fit(qmodel, datamodule=dm)
    print("QAT val acc:", model.val_accuracy.compute().item())

    # torch script saving
    smodel = model.to_torchscript()
    torch.jit.save(smodel, models+'audio_model_int8.pt')
    print("Validating quantized model:")
    trainer.validate(model)


def benchmark():
    # raspberry pi testing part from bottom of notebook
    import torch.utils.benchmark

    models_dir =  "./models/"

    # torch.backends.quantized.engine = 'qnnpack'
    torch.backends.quantized.engine = BACKEND

    fp_model = torch.jit.load(models_dir+'audio_model_fp32.pt', map_location='cpu')
    q_model = torch.jit.load(models_dir+'audio_model_int8.pt', map_location='cpu')

    inp = torch.randn(1, 1, 8000)

    tf = torch.utils.benchmark.Timer(
        setup='from __main__ import fp_model, inp',
        stmt='fp_model(inp)'
    )
    # due to the way PyTorch computes warmup, use >= 200 here to get at least two warmup steps
    print(f"fp32 {tf.timeit(200).median * 1000:.1f} ms")

    tq = torch.utils.benchmark.Timer(
        setup='from __main__ import q_model, inp',
        stmt='q_model(q_model.quant(inp))'
    )
    print(f"int8 {tq.timeit(200).median * 1000:.1f} ms")

if __name__ == "__main__":
    main()
    # benchmark()
