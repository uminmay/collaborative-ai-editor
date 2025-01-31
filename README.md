# README.md
# Collaborative AI Editor

A basic real-time code editor built with FastAPI and WebSockets.

## Setup

1. Clone the repository:
```bash
git clone git@github.com:uminmay/collaborative-ai-editor.git
cd collaborative-ai-editor
```

2. Build and run with Docker:
```bash
docker-compose up --build
```

The editor will be available at http://localhost:8000

## Development

- The editor files are stored in the `editor_files` directory
- Static files are in `app/static`
- Templates are in `app/templates`

## Deployment

The application is automatically deployed to GCP VM using GitHub Actions:
- Test environment: `/opt/test/collaborative-ai-editor`
- Production environment: `/opt/prod/collaborative-ai-editor`

Required GitHub Secrets:
- `GCP_SSH_PRIVATE_KEY`: SSH private key for GCP VM
- `GCP_VM_HOST`: GCP VM host address
- `GCP_VM_USERNAME`: GCP VM username

## Testing

Run tests with:
```bash
pytest
```


