"""AMS embedding model: paraphrase-multilingual-MiniLM-L12-v2, run locally with ONNX Runtime.

sentence-transformers cannot load here (Windows Application Control blocks the `regex` DLL that
`transformers` needs), so this module runs the official ONNX export of the same model with
`tokenizers` and applies the model's own pooling: the attention-masked mean of token embeddings,
max 128 tokens (1_Pooling/config.json, sentence_bert_config.json). Only AMS loads it (CLAUDE.md).

Download once from api/: uv run python -m app.ams_model
"""

from pathlib import Path

import httpx
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

REPO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"  # pinned so results are reproducible
FILES = ("onnx/model.onnx", "tokenizer.json")
MODEL_DIR = Path(__file__).resolve().parent.parent / ".models" / "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_VERSION = f"paraphrase-multilingual-MiniLM-L12-v2@{REVISION[:8]} (onnx)"
MAX_TOKENS = 128


def download(target: Path = MODEL_DIR) -> None:
    """Fetches the pinned model files (about 480 MB) unless they are already present."""
    for name in FILES:
        path = target / name
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(path.suffix + ".part")
        url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{name}"
        with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
            response.raise_for_status()
            with partial.open("wb") as out:
                for chunk in response.iter_bytes(1 << 20):
                    out.write(chunk)
        partial.replace(path)
        print(f"downloaded {name} ({path.stat().st_size / 1e6:.0f} MB)")


class Embedder:
    def __init__(self, model_dir: Path = MODEL_DIR) -> None:
        missing = [name for name in FILES if not (model_dir / name).exists()]
        if missing:
            raise FileNotFoundError(f"model files missing in {model_dir}: {missing}. Run: uv run python -m app.ams_model")
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(MAX_TOKENS)
        self.tokenizer.enable_padding()
        self.session = ort.InferenceSession(str(model_dir / "onnx" / "model.onnx"), providers=["CPUExecutionProvider"])
        self.input_names = {i.name for i in self.session.get_inputs()}

    def embed(self, texts: list[str]) -> np.ndarray:
        """One 384-dimension sentence embedding per text."""
        encodings = self.tokenizer.encode_batch(texts)
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self.input_names:
            feeds["token_type_ids"] = np.zeros_like(ids)
        tokens = self.session.run(None, feeds)[0]  # last_hidden_state: (batch, seq, 384)
        weights = mask[..., None].astype(np.float32)
        return (tokens * weights).sum(axis=1) / np.clip(weights.sum(axis=1), 1e-9, None)


if __name__ == "__main__":
    download()
