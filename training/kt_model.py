"""
Knowledge-tracing models.

KTTransformer — causal transformer over interaction tokens
  token_t = E[topic_t × response_t] + E[topic_t] + E[difficulty_t] + E[response_t] + E[gap_t] + E[pos_t]
  h_t     = causal self-attention encoder (pre-LN, SDPA, GELU MLP)
  p(correct at t+1 | query q) = sigmoid(MLP([h_t ; E_q[topic_q] + E_q[difficulty_q]]))
The query head lets one forward pass score *every* (topic, difficulty) pair for the
dashboard, and generalises SAKT/DKT-style heads.

DKT — Piech et al. (2015) LSTM baseline with the classic per-skill output layer.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class Block(nn.Module):
    def __init__(self, d, heads, dropout):
        super().__init__()
        self.heads = heads
        self.ln1 = nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Dropout(dropout), nn.Linear(4 * d, d))
        self.drop = nn.Dropout(dropout)
        self.attn_dropout = dropout

    def forward(self, x):
        B, L, D = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(D, dim=-1)
        q, k, v = (t.view(B, L, self.heads, D // self.heads).transpose(1, 2) for t in (q, k, v))
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True,
                                           dropout_p=self.attn_dropout if self.training else 0.0)
        x = x + self.drop(self.proj(a.transpose(1, 2).reshape(B, L, D)))
        return x + self.drop(self.mlp(self.ln2(x)))


class KTTransformer(nn.Module):
    def __init__(self, n_topics, n_diff, n_gap, max_len=200, d=256, layers=4, heads=8, dropout=0.1):
        super().__init__()
        self.n_topics, self.n_diff = n_topics, n_diff
        self.e_inter = nn.Embedding((n_topics + 1) * 3, d)
        self.e_topic = nn.Embedding(n_topics + 1, d)
        self.e_diff = nn.Embedding(n_diff, d)
        self.e_resp = nn.Embedding(3, d)
        self.e_gap = nn.Embedding(n_gap, d)
        self.e_pos = nn.Embedding(max_len, d)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList([Block(d, heads, dropout) for _ in range(layers)])
        self.ln_f = nn.LayerNorm(d)
        self.q_topic = nn.Embedding(n_topics, d)
        self.q_diff = nn.Embedding(n_diff, d)
        self.head = nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Dropout(dropout), nn.Linear(d, 1))

    def encode(self, topic, diff, resp, gap):
        L = topic.shape[1]
        pos = torch.arange(L, device=topic.device).unsqueeze(0)
        x = (self.e_inter(topic * 3 + resp) + self.e_topic(topic) + self.e_diff(diff)
             + self.e_resp(resp) + self.e_gap(gap) + self.e_pos(pos))
        x = self.drop(x)
        for blk in self.blocks:
            x = blk(x)
        return self.ln_f(x)

    def forward(self, topic, diff, resp, gap):
        """Teacher-forced training: position t predicts interaction t+1. Returns logits [B, L-1]."""
        h = self.encode(topic[:, :-1], diff[:, :-1], resp[:, :-1], gap[:, :-1])
        q = self.q_topic(topic[:, 1:].clamp(max=self.n_topics - 1)) + self.q_diff(diff[:, 1:])
        return self.head(torch.cat([h, q], dim=-1)).squeeze(-1)

    def predict_all(self, topic, diff, resp, gap):
        """Probabilities for every (topic, difficulty) as the next interaction: [B, n_topics, n_diff]."""
        h = self.encode(topic, diff, resp, gap)[:, -1]  # [B, d]
        q = self.q_topic.weight[:, None, :] + self.q_diff.weight[None, :, :]  # [T, Df, d]
        q = q.reshape(-1, q.shape[-1])  # [Q, d]
        B, Q = h.shape[0], q.shape[0]
        z = torch.cat([h[:, None, :].expand(B, Q, -1), q[None].expand(B, Q, -1)], dim=-1)
        return torch.sigmoid(self.head(z).squeeze(-1)).view(B, self.n_topics, self.n_diff)


class DKT(nn.Module):
    def __init__(self, n_topics, n_diff, n_gap=1, hidden=200, dropout=0.2, **_):
        super().__init__()
        self.n_topics, self.n_diff = n_topics, n_diff
        self.emb = nn.Embedding((n_topics + 1) * 3 * n_diff, hidden)
        self.lstm = nn.LSTM(hidden, hidden, batch_first=True)
        self.drop = nn.Dropout(dropout)
        self.out = nn.Linear(hidden, n_topics * n_diff)

    def forward(self, topic, diff, resp, gap):
        x = self.emb((topic[:, :-1] * 3 + resp[:, :-1]) * self.n_diff + diff[:, :-1])
        h, _ = self.lstm(x)
        logits = self.out(self.drop(h)).view(h.shape[0], h.shape[1], self.n_topics, self.n_diff)
        t = topic[:, 1:].clamp(max=self.n_topics - 1)
        logits = logits.gather(2, t[..., None, None].expand(-1, -1, 1, self.n_diff)).squeeze(2)
        return logits.gather(2, diff[:, 1:, None]).squeeze(-1)


class ExportWrapper(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, topic, difficulty, response, gap):
        return self.model.predict_all(topic, difficulty, response, gap)
