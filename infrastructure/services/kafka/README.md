# kafka

Kafka em KRaft (*Kafka Raft*, sem ZooKeeper) gerenciado pelo Strimzi: 3
brokers, cada um com seu volume EBS (*Elastic Block Store*), e o kafka-ui.
Os namespaces e NodePools `kafka-connect` e `kafka-streams` ficam prontos para
os workloads que consomem e produzem. Comandos no
[README da infraestrutura](../../README.md).

```mermaid
flowchart TB
  O[Strimzi operator] e1@--> K[3 brokers KRaft]
  K e2@--> V[(EBS gp3 de 20Gi<br/>por broker)]
  K e3@-->|roda em| N[NodePool kafka<br/>on-demand]
  C[kafka-connect] e4@-.-> K
  S[kafka-streams] e5@-.-> K
  U[kafka-ui:<br/>port-forward 8081] e6@--> K

  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
  e5@{ animate: true }
  e6@{ animate: true }

  classDef data fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef compute fill:#ffedd5,stroke:#ea580c,color:#7c2d12
  classDef orchestration fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
  classDef infra fill:#dcfce7,stroke:#16a34a,color:#14532d

  class V data
  class K,C,S compute
  class O,U orchestration
  class N infra
```

A UI (*User Interface*) do kafka-ui é acessada por `port-forward`.
