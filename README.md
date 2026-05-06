# Mini DBaaS for Rideshare

**Course:** 17CS352 - Cloud Computing,PES University 
**Project:** Class Project - Rideshare   

---

## Overview

This project implements a fault-tolerant, highly available Database-as-a-Service (DBaaS) for the RideShare application. The Users and Rides microservices route all database requests through a central orchestrator instead of calling the DB APIs on localhost. The orchestrator exposes the same read/write API interface, acting as a transparent and resilient database layer.

---

## Architecture

```
Users / Rides Microservices
            |
            v
    DBaaS Orchestrator
       /           \
      v             v
  WriteQ          ReadQ
 (Master)        (Slaves)
      |             |
      v             v
   DB Write      DB Read
      |
      v
   SyncQ ------> All Slaves (Eventual Consistency)
```

### Components

- **Orchestrator** - Central HTTP listener that receives requests from microservices and routes them to the appropriate RabbitMQ queues.
- **Master Worker** - Consumes write requests from `writeQ`, performs the DB write, and broadcasts updates to all slaves via `syncQ`.
- **Slave Workers** - Consume read requests from `readQ` and return results via `responseQ`. Multiple slaves run concurrently to handle parallel reads.
- **RabbitMQ** - Message broker managing `readQ`, `writeQ`, `syncQ`, and `responseQ`.
- **ZooKeeper** - Handles distributed coordination and slave leader election using ephemeral znodes.
- **Docker SDK** - Used by the orchestrator to spawn or kill slave containers dynamically.

---

## Features

- **Fault Tolerance** - ZooKeeper monitors slaves via ephemeral znodes. When a slave goes down, the watch function in the orchestrator automatically spawns a replacement and syncs data asynchronously.
- **High Availability** - Read requests are distributed across multiple slave workers. Messages in `readQ` are persistent so that if one slave is busy, another picks up the next message.
- **Eventual Consistency** - All write operations are broadcast to slaves via `syncQ` to keep data consistent across workers.
- **Auto-Scaling** - A background thread calls the `scale()` function every 2 minutes, spawning or killing slave containers based on the volume of incoming read requests.
- **Crash APIs** - Dedicated endpoints to simulate master and slave crashes for fault tolerance testing.
- **Worker List API** - Returns a live list of currently running worker containers.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| RabbitMQ | Message queuing for read, write, and sync operations |
| Apache ZooKeeper (Kazoo) | Distributed coordination and slave leader election |
| Docker SDK (docker-py) | Dynamic container lifecycle management |
| Flask | REST API layer |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/db/write` | Route a write request to the master worker |
| GET | `/api/v1/db/read` | Route a read request to an available slave |
| POST | `/api/v1/crash/master` | Terminate the master container |
| POST | `/api/v1/crash/slave` | Terminate the slave with the highest PID |
| GET | `/api/v1/worker/list` | Return a list of active worker containers |
| POST | `/api/v1/db/clear` | Clear the database |

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.x
- RabbitMQ
- Apache ZooKeeper

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/mini-dbaas-rideshare.git
   cd mini-dbaas-rideshare
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start ZooKeeper and RabbitMQ:
   ```bash
   docker-compose up -d zookeeper rabbitmq
   ```

4. Start the orchestrator:
   ```bash
   python orchestrator.py
   ```

5. Start the master worker:
   ```bash
   python worker.py --role master
   ```

6. Start one or more slave workers:
   ```bash
   python worker.py --role slave
   ```

---

## Team Contributions

| Name | Contribution |
|---|---|
| Pratheek Kamath M | RabbitMQ integration (readQ, writeQ, syncQ, responseQ) |
| Radhika Sadanand | Crash APIs and Worker List API |
| Varsha C | Auto-scaling logic using Docker SDK |
| Namana | Slave leader election using ZooKeeper |

---

## References

- RabbitMQ Documentation: https://www.rabbitmq.com/getstarted.html
- Kazoo (ZooKeeper Python client): https://kazoo.readthedocs.io/en/latest/
- Docker SDK for Python: https://docker-py.readthedocs.io/en/stable/
