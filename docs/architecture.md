# Architecture and data flow

```mermaid
flowchart TB
  subgraph Sources
    S1[Source registry]
    S2[Public/openly licensed data]
    S3[Synthetic smoke data]
  end
  subgraph Processing
    B[Bronze: immutable JSONL]
    M[Silver: normalized text + provenance]
    G[Gold: leakage-safe parallel splits]
  end
  subgraph Retrieval
    L[BM25 lexical index]
    D[Dense encoder/index]
    H[Hybrid RRF]
    T[Translation / alignment mitigation]
  end
  subgraph Evidence
    Q[Recall@k, MRR, nDCG@10]
    A[Answer quality]
    F[Language gap + CI]
    C[Cost, latency, storage]
    P[Partition / Spark scale evidence]
  end
  S1 --> S2 --> B --> M --> G
  S3 --> B
  G --> L --> H
  G --> D --> H
  G --> T --> H
  H --> Q
  H --> A
  Q --> F
  A --> F
  H --> C
  G --> P
  F --> R[Notebook, report, cards, demo]
  C --> R
  P --> R
```

## Storage layers

- **Bronze:** source rows retained with source ID, license status and retrieval timestamp.
- **Silver:** normalized Unicode text, language tag, document ID, topic ID and provenance.
- **Gold:** query/document pairs with leakage-safe split, answer key and evaluation metadata.

The smoke runner uses local JSONL for portability. The optional Spark runner demonstrates the same logical stages with repartitioned input and records partition count and elapsed time.

