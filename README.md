# 🚀 Schedule Helper

### AI-Powered Cognitive Assistant for Smarter Workflows

**Schedule Helper** is an AI-driven task and decision management platform designed to reduce *cognitive overload* and *decision fatigue* in modern digital work environments.

Instead of acting as a traditional task manager, it functions as a **context-aware decision assistant**—adapting to the user’s energy level, emotional state, and real-time context to generate realistic and actionable plans.

---

## 📌 Project Overview

This project is part of the **Jalin AI Services Platform** initiative in collaboration with **PT. Jalin Mayantara Indonesia**.

The goal is to build an **integrated AI platform** that enhances operational efficiency and supports intelligent decision-making across workflows.

---

## 🎯 Key Problems Addressed

### 1. Lack of Integrated AI Platform

Eliminates duplicated AI development efforts by introducing a standardized **abstraction layer**.

### 2. High Cognitive Load

Helps users organize scattered thoughts using a structured **mind dump processing system**.

### 3. Unrealistic Prioritization

Generates plans based on **user condition (energy & mental state)** instead of relying solely on deadlines.

---

## 🏗️ System Architecture

The system follows a **Layered Architecture** to ensure scalability, maintainability, and modularity.

```
Client Layer (Next.js)
        ↓
API Gateway (Nest.js)
        ↓
Application Layer (Core Logic)
        ↓
AI Service Layer (LLM + RAG)
        ↓
Data Layer (SQL + Vector DB)
```

### Architecture Breakdown:

* **Client Layer**
  Built with **Next.js**, providing an intuitive chat-based interface.

* **API Layer**
  Powered by **Nest.js**, handling request routing, validation, and security.

* **Application Layer**
  Core business logic including:

  * Context Builder
  * Planner Engine
  * Action Generator

* **AI Service Layer**
  Orchestrates LLM interactions and Retrieval-Augmented Generation (RAG).

* **Data Layer**

  * Structured data: **PostgreSQL**
  * Semantic data: **ChromaDB (Vector Database)**

---

## 🤖 Multi-Agent Workflow (LangChain Orchestration)

The system leverages a **multi-agent architecture** powered by LangChain:

### 1. Mind Dump Interpreter

Transforms unstructured user input into a standardized JSON format.

### 2. Context-Aware Prioritizer

Applies quantitative scoring (urgency, impact, energy) to select the top 1–3 priorities.

### 3. Action Translator

Breaks down priorities into **immediate, executable steps (quick wins)**.

---

## 🛠️ Tech Stack

| Layer             | Technology          |
| :---------------- | :------------------ |
| **Frontend**      | Next.js (Vercel)    |
| **Backend API**   | Nest.js             |
| **AI Model**      | GPT-4o (OpenAI)     |
| **Orchestration** | LangChain           |
| **Database**      | PostgreSQL (NeonDB) |
| **Vector Store**  | ChromaDB            |

---

## 👥 Team (Pencuci Ompreng MBG 😄)

| Name                            | Role                                |
| :------------------------------ | :---------------------------------- |
| **M. Dhifan Rizky Wardana**     | Service Design & Governance Lead    |
| **Muhammad Raka Fadillah**      | AI Orchestrator & Agent Engineer    |
| **Naufan Ahnaf**                | AI Pipeline & Optimization Engineer |
| **Shatara Belva Maritza**       | AI Integration Logic Engineer       |
| **M. Rendy Adhi Pradana N. H.** | AI Interface & Inference Engineer   |
| **Delfan Zuffar Rajjaz Nuziar** | Platform & Infrastructure Engineer  |

---

## 🧠 Key Value Proposition

* 🧩 **Context-Aware Planning** — Not just tasks, but realistic execution
* ⚡ **Action-Oriented Output** — Focus on immediate, doable steps
* 🧠 **Cognitive Load Reduction** — Externalizes thinking into structured plans
* 🔗 **Unified AI Platform** — Reduces fragmentation in AI development

---

## 📄 License

This project is developed by students of **Faculty of Computer Science, Universitas Brawijaya** in collaboration with **PT. Jalin Mayantara Indonesia**.
