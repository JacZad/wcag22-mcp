#!/usr/bin/env python3
"""Test the KaLM-Embedding-Gemma3-12B MLX model for embedding quality."""

import time, sys
import mlx.core as mx
from mlx_lm import load, generate

MODEL = "thedarkstar/KaLM-Embedding-Gemma3-12B-2511-mlx-4Bit"

TEST_TEXTS = [
    "Requires touch targets to be at least 24 by 24 CSS pixels.",
    "Success Criterion 2.5.8 Target Size Minimum",
    "Focus indicator must have a minimum area and contrast ratio.",
    "Text must have a contrast ratio of at least 4.5 to 1 against its background.",
    "All functionality must be operable through a keyboard interface.",
]

print(f"Loading {MODEL}...")
t0 = time.time()
model, tokenizer = load(MODEL)
print(f"Loaded in {time.time()-t0:.1f}s")

# Get hidden dimension from model config
hidden_dim = 3840  # Gemma3 12B

# Peek at model structure
print(f"\nModel: {type(model).__name__}")
if hasattr(model, 'model'):
    inner = model.model
    print(f"  .model: {type(inner).__name__}")
    print(f"  .model.layers: {len(inner.layers)} layers")
    if hasattr(inner, 'norm'):
        print(f"  .model.norm: {type(inner.norm).__name__}")
    if hasattr(inner, 'embed_tokens'):
        print(f"  .model.embed_tokens: ✓")
if hasattr(model, 'layers'):
    print(f"  .layers: {len(model.layers)}")

def embed_text(text: str) -> mx.array:
    """Get embedding via last hidden state mean pooling."""
    tokens = tokenizer.encode(text)
    # Limit length
    if len(tokens) > 1024:
        tokens = tokens[:1024]
    x = mx.array([tokens])
    
    # Forward pass - for Gemma MLX, the model returns (logits, cache)
    # logits shape: [1, seq_len, vocab_size]
    # We need hidden states from before the lm_head
    
    # Try: access model.model output directly
    inner = model.model if hasattr(model, 'model') else model
    
    # For MLX Gemma, forward is: embed → layers → norm → lm_head
    # Let's get the hidden state after norm but before lm_head
    h = inner.embed_tokens(x)
    mask = None  # causal mask not needed for embedding
    
    for layer in inner.layers:
        h = layer(h, mask=mask)
    h = inner.norm(h)
    # h shape: [1, seq_len, hidden_dim]
    
    # Mean pooling (excluding padding tokens if any)
    embedding = h.mean(axis=1)  # [1, hidden_dim]
    return embedding

print("\nGenerating embeddings for test texts...")
embeddings = []
for text in TEST_TEXTS:
    emb = embed_text(text)
    embeddings.append(emb)
    vec = emb[0]  # first (only) item in batch
    top5 = vec[:5].tolist()
    print(f"  [{len(emb[0])}d] ...{', '.join(f'{v:.4f}' for v in top5)}  |  {text[:60]}")

# Compare similarities
print("\n=== Cosine Similarities ===")
# Target size texts should be close to each other
sim_1_2 = mx.sum(embeddings[0] * embeddings[1]) / (mx.linalg.norm(embeddings[0]) * mx.linalg.norm(embeddings[1]))
sim_1_3 = mx.sum(embeddings[0] * embeddings[2]) / (mx.linalg.norm(embeddings[0]) * mx.linalg.norm(embeddings[2]))
sim_3_4 = mx.sum(embeddings[2] * embeddings[3]) / (mx.linalg.norm(embeddings[2]) * mx.linalg.norm(embeddings[3]))
sim_1_4 = mx.sum(embeddings[0] * embeddings[3]) / (mx.linalg.norm(embeddings[0]) * mx.linalg.norm(embeddings[3]))

print(f"  2.5.8 vs 2.5.8 (title):     {sim_1_2.item():.4f}  (expect high)")
print(f"  2.5.8 vs 2.4.13 (focus):    {sim_1_3.item():.4f}  (expect low)")
print(f"  2.4.13 vs 1.4.3 (contrast): {sim_3_4.item():.4f}  (expect medium - both about visual)")
print(f"  2.5.8 vs 1.4.3 (unrelated): {sim_1_4.item():.4f}  (expect low)")

# Also test with technique description
tech_text = "G210: Using a control to allow access to content in different orientations."
emb_tech = embed_text(tech_text)
sim_tech_focus = mx.sum(emb_tech * embeddings[2]) / (mx.linalg.norm(emb_tech) * mx.linalg.norm(embeddings[2]))
sim_tech_ref = mx.sum(emb_tech * embeddings[0]) / (mx.linalg.norm(emb_tech) * mx.linalg.norm(embeddings[0]))
print(f"  G210 vs 2.4.13 (focus):    {sim_tech_focus.item():.4f}")
print(f"  G210 vs 2.5.8 (target):    {sim_tech_ref.item():.4f}")

# Memory usage
import psutil
proc = psutil.Process()
print(f"\nMemory: {proc.memory_info().rss / 1024**3:.1f} GB")
print(f"Time: {time.time()-t0:.1f}s")
