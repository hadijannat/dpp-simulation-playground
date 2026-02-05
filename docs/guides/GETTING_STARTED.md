# Getting Started

1. Copy environment defaults:

```
cp infrastructure/docker/.env.example infrastructure/docker/.env
```

2. Start the stack:

```
make up
```

3. Run migrations:

```
make migrate
```

4. Seed initial data:

```
make seed
```
