## Installation

Clone this repository into your local system

1: Create a virtual environment

```bash
  python -m venv .venv (MacOSX)
  source .venv/bin/active
```

2: Install all neccessary requirements

```bash
  pip install -r requirements.txt
```

3: Create a .env file which will store your OPENAI_API_KEY

```bash
  OPENAI_API_KEY = "sk-..."
```

## Running the code

Once all the steps are completed

1: Run the code using the terminal with the command

```bash
  uvicorn src.app:app --reload
```
