# 🤖 AI Client Operations Manager 

An autonomous, multi-agent platform designed to act as a virtual employee for freelancers, agencies, and software development companies. 
Visit: https://clientmanger.tech/docs

<img width="1440" height="900" alt="Screenshot 2026-06-21 at 11 20 46 PM" src="https://github.com/user-attachments/assets/09adac84-b059-4b62-a512-c7fb6e300c79" />

The AI Client Operations Manager seamlessly assumes the roles of an Account Manager, Project Coordinator, and Client Success Representative. By automating client communication, requirement gathering, project estimation, and team capacity planning, this system drastically reduces operational overhead while delivering instant, intelligent responses to clients.

## Problem & Solution

Freelancers and agencies frequently lose leads due to slow response times and spend excessive hours parsing complex requirement documents, scheduling discovery calls, and compiling project status updates. 

This platform solves these bottlenecks by deploying specialized AI agents that integrate directly with internal project management systems (like GitHub and Jira) to autonomously handle client-facing operations.

## Core Features

* **Intelligent Requirement Intake:** Converses with potential clients to extract budgets, timelines, and technical needs, outputting a structured project specification.
* **Omnichannel Summarization:** Ingests chat conversations, long documents, and voice recordings to generate comprehensive functional requirements and risk assessments.
* **Timeline & Capacity Engine:** Analyzes team skill distribution, existing workloads, and historical data to generate accurate timelines, resource requirements, and automated proposals.
* **Proactive Project Updates:** Collects live data from internal task systems to generate human-readable progress reports.
* **Risk Detection & Alerts:** Monitors progress rates and blocked tasks, generating proactive alerts if project completion probability drops.
* **Voice Discovery & Scheduling:** Autonomously handles discovery calls, updates the CRM, checks calendar availability, and books meetings.


### Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **AI Layer** | PydanticAI | Agent workflows, tool calling, and structured outputs. |
| **LLM Model** | Fine-Tuned Gemini | Custom-trained reasoning engine for highly contextual client interactions and accurate data extraction. |
| **Backend** | Python, FastAPI | High-performance, asynchronous API gateway and service communication. |
| **Frontend** | Flutter | Cross-platform client dashboards and admin interfaces. |
| **NoSQL Database** | Azure Cosmos DB | High-throughput storage for massive chat histories, maintaining long-term memory and project requirements. |
| **Relational Database**| PostgreSQL | Secure storage for structured entity data, including client account details and payment information. |
| **Cache** | Redis | Low-latency short-term memory buffer for active agent conversations. |
| **Infrastructure** | Docker, Kubernetes | Containerized deployment ensuring horizontal scalability and robust orchestration. |

## Getting Started

### Prerequisites
* Docker & Kubernetes (Minikube or Cloud Provider)
* Gemini API Key (with access to your fine-tuned model)
* Azure Cosmos DB Connection String
* PostgreSQL instance
* Redis instance

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/ai-client-manager.git](https://github.com/yourusername/ai-client-manager.git)
   cd ai-client-manager

2. **Configure Environment Variables:**
   ```bash
   ACCESS_TOKEN_EXPIRE_MINUTES=30
    AZURE_DB_USER=db_user
    AZURE_DB_PASSWORD=password
    AZURE_DB_HOST=host
    AZURE_DB_NAME=db_name
    COSMOS_ENDPOINT=endpoint
    COSMOS_KEY=cosmos_key
    COSMOS_DATABASE=db
    GEMINI_API_KEY=your_fine_tuned_key  
