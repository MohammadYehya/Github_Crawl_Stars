# Github_Crawl_Stars
This project implements a crawler that collects metadata (repo stars) for 100,000 GitHub repositories using the GraphQL API. It stores this data in a PostgreSQL schema, handles rate limits, and runs end-to-end in a CI pipeline without requiring any elevated permissions.\
The full task can be viewed at [Task.md](Task.md).

## Project Structure
```py
├── crawler/
│   ├── main.py                 # Crawler logic
│   ├── Postgres_DB_Setup.py    # Database and schema setup
│   └── Github_Client.py        # GitHub API wrapper
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions pipeline
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Code Explanation
Firstly, the code provided in the repository is meant to be used in a Github Actions Pipeline, therefore any issues that occur in local development are beyond the issues of this repository. To replicate the results of the project, simply clone the repository and trigger a workflow, and you should have a csv file as an output artifact.

- Do something

The existing Github Action Workflows can be found [Here](https://github.com/MohammadYehya/Github_Crawl_Stars/actions/workflows/main.yml).

## What Would I Do Differently for 500M Repositories?
For a giant-scale crawl over github, I would propose a distributed/parallel architecture over a single client solution. However, the current solution implements technique which can only be performed sequentially.\
Therefore, a hybrid solution would be imposed in which multiple ranges/slices of stars would be divided into different threads/distributed nodes, which would then perform the sequential crawl.

## How Will the Schema Evolve for More Metadata?
To support richer metadata like issues, pull requests, and comments, we can normalize and introduce different tables to store other sorts of data. For instance, a table for storing pull requests for a certain repository would be as follows:
```postgresql
CREATE TABLE pull_requests (
    id BIGINT PRIMARY KEY,
    repo_id BIGINT REFERENCES repositories(id),
    title TEXT,
    state TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```