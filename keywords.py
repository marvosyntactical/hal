import torch
import pytorch_lightning as pl

class KWModel:
    pass

if __name__ == "__main__":
    # raspberry pi testing part from bottom of notebook
    import torch.utils.benchmark

    models_dir =  "./models/"

    torch.backends.quantized.engine = 'fbgemm'

    fp_model = torch.jit.load(models_dir+'audio_model_fp32.pt', map_location='cpu')
    q_model = torch.jit.load(models_dir+'quantized_2d_model.pt', map_location='cpu')

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
