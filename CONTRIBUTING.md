# Contributing to LeadSniper

First off, thanks for taking the time to contribute to the M4STCLAW mesh! 

The LeadSniper architecture is heavily integrated with the overall DAG topology. When contributing, please ensure you adhere to our enterprise standards.

## Development Workflow

1. **Fork the repo** and clone it locally.
2. **Install dev dependencies**: `pip install -e .[dev]`
3. **Branch**: Create a feature branch `git checkout -b feature/your-feature-name`
4. **Code**: Adhere to PEP-8. Run `black src/` to format.
5. **Test**: All changes must pass `pytest`.
6. **Pull Request**: Open a PR using the provided template.

## Architectural Guidelines

- **No Blocking Calls**: Any I/O operations (scraping, SMTP) must be asynchronous or threaded to prevent locking the main execution DAG.
- **Fail Gracefully**: If an API key rotates or a proxy dies, the system must catch the exception and switch to the failover pool autonomously.
- **LLM Agnosticism**: If modifying the intent-scoring pipeline, ensure your code abstracts the model provider so we can swap OpenAI for Claude/Llama instantly.

By contributing, you agree that your code will be licensed under the MIT License.
