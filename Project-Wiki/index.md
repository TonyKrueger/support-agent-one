---
title: Support Agent Project Wiki
description: Central documentation for the Support Agent project
date_created: 2025-04-09
last_updated: 2025-04-17
sidebar_position: 0
---

# Support Agent Project Wiki

Welcome to the Support Agent Project Wiki. This documentation provides comprehensive information about the project's architecture, components, and implementation details.

## Documentation Index

### System Architecture
* [System Overview](SystemOverview.md)
* [Database Schema](DatabaseSchema.md)
* [API Documentation](API.md)

### Core Components
* [Document Processing](DocumentProcessing.md)
* [Application Layer Chunking](ApplicationLayerChunking.md)
* [Document Management](DocumentManagement.md)
* [Vector Search](VectorSearch.md)
* [Observability System](Observability.md)
* [Chat Interface](ChatInterface.md)
* [Conversation Management](ConversationManagement.md)
* [Agent System](AgentSystem.md)

### Integrations
* [OpenAI Integration](OpenAI.md)
* [Supabase Integration](Supabase.md)

### Development
* [Development Setup](DevelopmentSetup.md)
* [Testing Guidelines](TestingGuidelines.md)
* [Deployment Process](Deployment.md)

### Usage
* [User Guide](UserGuide.md)
* [Administration](Administration.md)
* [Troubleshooting](Troubleshooting.md)

## Using This Wiki

New pages should be created using the [template](template.md) for consistency.

Each document should:
1. Start with a clear title and overview
2. Include relevant code examples where appropriate
3. Link to related documents
4. Include a "last updated" date when making significant changes

## Last Updated
Date: 2025-04-17

## Getting Started

To get started with the project:

1. Review the [project plan](../Plan.md) for an overview
2. Set up the database infrastructure as documented in [Supabase Setup](./Supabase.md)
3. Configure the OpenAI integration as described in the [OpenAI documentation](./OpenAI.md)
4. Learn about the document processing pipeline in the [Document Processing](./DocumentProcessing.md) guide
5. Follow the implementation tasks in [Tasks](../Tasks.md)

## Contributing to Documentation

When adding to this documentation:

1. Follow the established format with YAML front matter
2. Include clear, concise explanations with code examples where appropriate
3. Update the index.md file when adding new documentation pages
4. Keep the "last_updated" field current in the front matter 