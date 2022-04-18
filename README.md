# Ribes RPC
[![Latest PyPI package version](https://badge.fury.io/py/ribes.svg)](https://pypi.org/project/ribes)  
Async framework for JSON-RPC via RabbitMQ

## Key feature
* Implements JSON-RPC via RabbitMQ RPC
* Full support to asyncio
* Simple configuration
* Integrates to existing framework like FastAPI or Sanic
* Full support to Pydantic objects as parameters

## Installation
```shell
pip install ribes
```

## Getting started
Create server handler:
```python
app = Ribes("application")

@app.register(name="namespace.method")
async def method(a, b):
    ...
```

Call method from client
```python
app = Ribes("application")

method = app.caller("namespace.method")

result = await method(1, 2)
```

## To Do
* Documentation and examples

## Requirements
* Python >= 3.8
* RabbitMQ

## License
`ribes` is offered under the Apache 2 license.

## Source code
The latest developer version is available in a GitHub repository:
<https://github.com/aiselis/ribes>