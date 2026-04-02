# Contributing to CineCraft

Thank you for your interest in contributing to CineCraft! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/CineCraft.git
cd CineCraft
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 3. Set Up Development Environment
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Make Your Changes
- Keep commits atomic and focused
- Write clear commit messages
- Follow existing code style

### 5. Test Your Changes
```bash
python main.pyw
# Test the feature manually
```

### 6. Submit Pull Request
- Write a clear PR title and description
- Reference any related issues (#123)
- Ensure all changes are working

## Development Guidelines

### Code Style

**Python**
- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small

**JavaScript**
- Use semicolons
- Use `const`/`let` instead of `var`
- Write clear, descriptive names
- Comment complex logic

**CSS**
- Use semantic class names
- Keep selectors simple
- Comment sections
- Follow mobile-first approach

### Commit Messages

```
feat: Add new feature description
fix: Correct specific issue
docs: Update documentation
style: Format code (no logic change)
refactor: Reorganize code structure
test: Add or update tests
```

### Pull Request Process

1. **Before submitting:**
   - [ ] Code follows style guidelines
   - [ ] Changes tested locally
   - [ ] README updated if needed
   - [ ] No unnecessary dependencies added

2. **PR Description should include:**
   - What problem does it solve?
   - How was it tested?
   - Any breaking changes?
   - Screenshots for UI changes

3. **Review process:**
   - Maintainers will review your PR
   - Address feedback constructively
   - Be patient - reviews take time

## Areas for Contribution

### Easy (Good for beginners)
- Documentation improvements
- Bug fixes with clear reproduction steps
- UI/UX improvements
- README updates

### Medium
- New file format support
- Performance optimizations
- Additional error handling
- Code refactoring

### Hard
- New major features
- Architecture changes
- Cross-platform support
- Plugin system implementation

## Reporting Bugs

### Before Reporting
- [ ] Check existing issues
- [ ] Try reproducing in latest version
- [ ] Verify it's not a local setup issue

### Bug Report Template
```markdown
**Describe the bug**
Clear description of what's wrong

**Steps to reproduce**
1. Do this
2. Then this
3. See error

**Expected behavior**
What should happen

**Environment**
- OS: Windows 11
- Python: 3.13
- CineCraft version: 1.0

**Screenshots**
If applicable, add screenshots
```

## Suggesting Features

### Before Suggesting
- [ ] Check if feature already exists
- [ ] Check existing issues/discussions
- [ ] Verify it aligns with project scope

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What should the feature do?

**Describe alternatives considered**
Other solutions you thought of

**Additional context**
Any other information
```

## Project Structure Reference

```
CineCraft/
├── main.pyw              # Entry point - modify carefully
├── app.py                # FastAPI routes - most backend work here
├── ui/
│   ├── index.html        # Structure - add UI elements here
│   ├── script.js         # Logic - add interactivity here
│   └── style.css         # Styling - add CSS here
└── requirements.txt      # Dependencies - update for new packages
```

## Common Tasks

### Adding a New Tool/Feature

1. **Backend** (`app.py`):
   ```python
   @app.post("/process/newtool")
   async def process_newtool(request: dict):
       # Implement FFmpeg command
       return {"result": "success"}
   ```

2. **Frontend** (`ui/index.html`):
   ```html
   <button class="tool-link-card" data-route="newtool">
       New Tool
   </button>
   ```

3. **Logic** (`ui/script.js`):
   ```javascript
   async function runNewTool() {
       // Call backend API
       const response = await fetch("/process/newtool");
   }
   ```

### Adding Support for New Format

1. Update `DialogBridge._dialog()` file type filters
2. Add format handling in `app.py`
3. Test with sample files
4. Update README supported formats

### Styling Changes

1. Edit `ui/style.css`
2. Use existing CSS variables
3. Test responsiveness
4. Submit with before/after screenshots

## Testing Before Submission

```bash
# Run application
python main.pyw

# Test in browser (dev mode)
python app.py
# Visit http://localhost:8000

# Build executable
pyinstaller CineCraft.spec --clean
# Test dist/CineCraft/CineCraft.exe
```

## Getting Help

- **Questions?** Create a Discussion on GitHub
- **Stuck?** Comment on related issues
- **Need advice?** Check existing discussions
- **Quick help?** Join our community

## Recognition

Contributors will be:
- Listed in project contributors
- Credited in release notes
- Recognized for significant contributions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for making CineCraft better!** 🎬✨
