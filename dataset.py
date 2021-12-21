import os
from typing import Tuple, Optional, Union
from pathlib import Path

import torchaudio
from torch.utils.data import Dataset
from torch import Tensor

EXCEPT_FOLDER = "_background_noise_"
FOLDER_IN_ARCHIVE = "hal_keywords"

def _load_list(root, *filenames):
    output = []
    for filename in filenames:
        filepath = os.path.join(root, filename)
        with open(filepath) as fileobj:
            output += [os.path.normpath(os.path.join(root, line.strip())) for line in fileobj]
    return output


def low_hal_kw_item(filepath: str, path: str) -> Tuple[Tensor, int, str, str, int]:
    relpath = os.path.relpath(filepath, path)
    label, filename = os.path.split(relpath)
    stub, ext = filename.split(".")
    # Besides the officially supported split method for datasets defined by "validation_list.txt"
    # and "testing_list.txt" over "speech_commands_v0.0x.tar.gz" archives, an alternative split
    # method referred to in paragraph 2-3 of Section 7.1, references 13 and 14 of the original
    # paper, and the checksums file from the tensorflow_datasets package [1] is also supported.
    # Some filenames in those "speech_commands_test_set_v0.0x.tar.gz" archives have the form
    # "xxx.wav.wav", so file extensions twice needs to be stripped twice.
    # [1] https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/url_checksums/speech_commands.txt
    utterance_number = int(stub)
    # Load audio
    waveform, sample_rate = torchaudio.load(filepath)
    return waveform, sample_rate, label, utterance_number

class HAL_KW_DATASET(Dataset):
    """Create a Dataset for Hal9k Commands.
    root (str or Path): Path to the directory where the dataset is found.
    or the type of the dataset to dowload.
    Allowed type values are ``"speech_commands_v0.01"`` and ``"speech_commands_v0.02"``
    (default: ``"speech_commands_v0.02"``)
    folder_in_archive (str, optional):
    The top-level directory of the dataset. (default: ``"SpeechCommands"``)
    subset (str or None, optional):
    Select a subset of the dataset [None, "training", "validation", "testing"]. None means
    the whole dataset. "validation" and "testing" are defined in "validation_list.txt" and
    "testing_list.txt", respectively, and "training" is the rest. Details for the files
    "validation_list.txt" and "testing_list.txt" are explained in the README of the dataset
    and in the introduction of Section 7 of the original paper and its reference 12. The
    original paper can be found `here <https://arxiv.org/pdf/1804.03209.pdf>`_. (Default: ``None``)
    """
    def __init__(self,
            root: Union[str, Path],
            folder_in_archive: str = FOLDER_IN_ARCHIVE,
            subset: Optional[str] = None,
        ) -> None:
        assert subset is None or subset in ["training", "validation", "testing"]
        "When `subset` not None, it must take a value from "
        # Get string representation of 'root' in case Path object is passed

        root = os.fspath(root)

        self._path = os.path.join(root, folder_in_archive)
        if subset == "validation":
            self._walker = _load_list(self._path, "validation_list.txt")
        elif subset == "testing":
            self._walker = _load_list(self._path, "testing_list.txt")
        elif subset == "training":
            excludes = set(_load_list(self._path, "validation_list.txt", "testing_list.txt"))
            walker = sorted(str(p) for p in Path(self._path).glob('*/*.wav'))
            self._walker = [
                w for w in walker
                if  os.path.normpath(w) not in excludes
            ]
        else:
            walker = sorted(str(p) for p in Path(self._path).glob('*/*.wav'))
            self._walker = [w for w in walker if EXCEPT_FOLDER not in w]

    def __getitem__(self, n: int) -> Tuple[Tensor, int, str, str, int]:
        """Load the n-th sample from the dataset.
        Args:
        n (int): The index of the sample to be loaded
        Returns:
        (Tensor, int, str, str, int):
        ``(waveform, sample_rate, label, speaker_id, utterance_number)``
        """
        fileid = self._walker[n]
        return low_hal_kw_item(fileid, self._path)

    def __len__(self) -> int:
        return len(self._walker)


def main():
    DATASET = HAL_KW_DATASET("data")

if __name__ == "__main__":
    main()
