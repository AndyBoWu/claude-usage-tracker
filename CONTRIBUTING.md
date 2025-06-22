# Contributing to Claude Usage Tracker

First off, thank you for considering contributing to Claude Usage Tracker! It's people like you that make this tool better for everyone.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include details about your configuration and environment**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the existing style
5. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/claude-usage-tracker.git
cd claude-usage-tracker

# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Code Style

- Follow PEP 8
- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused
- Write docstrings for all functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage

## Areas for Contribution

### High Priority
- **Export functionality**: CSV/JSON export of usage data
- **Performance optimization**: Handle very large conversation histories
- **Cross-platform support**: Windows/Linux menu bar widgets

### Medium Priority
- **Web dashboard**: Browser-based usage visualization
- **More analytics**: Deeper insights into usage patterns
- **Configuration file**: User preferences and settings

### Nice to Have
- **Themes**: Different color schemes for output
- **Notifications**: Alert when hitting usage thresholds
- **Integration**: With other developer tools

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you! 🙏