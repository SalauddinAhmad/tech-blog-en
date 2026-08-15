# Contributing to Tech Blog (EN)

Thanks for your interest in contributing! This is a [Hugo](https://gohugo.io/) static site.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork locally
3. Install [Hugo extended](https://gohugo.io/installation/) (v0.120+)
4. Run `hugo server` and open `http://localhost:1313`

## Adding Content

- Blog posts go in `content/en/posts/` as Markdown files.
- Use `hugo new posts/your-post-slug.md` to scaffold a post.
- Front matter follows the existing pattern (title, date, tags, etc.).

## Style Guide

- **Writing:** Clear, concise English. Avoid jargon; explain technical terms when needed.
- **Code:** Follow the existing formatting. Use fenced code blocks with language hints.
- **Images:** Place in `static/img/` or `assets/` (for Hugo image processing).

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add article about X
fix: correct broken link in Y
docs: update README
core: refactor template Z
```

## Pull Requests

1. Create a feature branch from `main`.
2. Make your changes and commit with clear messages.
3. Open a PR with a brief description of what changed and why.
4. Ensure `hugo build` succeeds before submitting.

## Reporting Issues

Please open a GitHub issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Browser/device info (if applicable)

## License

All contributions are made under the [MIT License](LICENSE).
