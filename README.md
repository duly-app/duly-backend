# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/duly-app/duly-backend/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                       |    Stmts |     Miss |   Cover |   Missing |
|----------------------------------------------------------- | -------: | -------: | ------: | --------: |
| src/\_\_init\_\_.py                                        |        0 |        0 |    100% |           |
| src/adapters/\_\_init\_\_.py                               |        3 |        0 |    100% |           |
| src/adapters/orm/\_\_init\_\_.py                           |        5 |        0 |    100% |           |
| src/adapters/orm/base.py                                   |        4 |        0 |    100% |           |
| src/adapters/orm/mappers.py                                |       13 |        4 |     69% | 12, 18-20 |
| src/adapters/orm/notes.py                                  |        6 |        0 |    100% |           |
| src/adapters/orm/users.py                                  |       39 |        6 |     85% |25, 33, 44, 54, 63, 71 |
| src/adapters/repository/\_\_init\_\_.py                    |        8 |        0 |    100% |           |
| src/adapters/repository/notes\_event\_store.py             |        8 |        0 |    100% |           |
| src/adapters/repository/notes\_projection.py               |       17 |        0 |    100% |           |
| src/adapters/repository/notes\_repo.py                     |       31 |        1 |     97% |        56 |
| src/adapters/repository/sqlalchemy\_notes\_event\_store.py |       39 |       15 |     62% |21-34, 38, 90, 94, 104-107, 112-118 |
| src/adapters/repository/sqlalchemy\_notes\_projection.py   |       34 |       16 |     53% |21, 36, 57-65, 70-83, 93-107 |
| src/adapters/repository/sqlalchemy\_user\_repo.py          |       26 |        7 |     73% |14, 24, 29-34, 40 |
| src/adapters/repository/user\_repo.py                      |       21 |        6 |     71% |9, 13, 17, 21, 25, 29 |
| src/adapters/security/\_\_init\_\_.py                      |        5 |        0 |    100% |           |
| src/adapters/security/argon\_password\_service.py          |       13 |        6 |     54% |11, 14, 17-20 |
| src/adapters/security/jwt\_codec.py                        |       16 |        0 |    100% |           |
| src/adapters/security/password\_service.py                 |        8 |        2 |     75% |     7, 11 |
| src/adapters/security/service\_token\_service.py           |       16 |        1 |     94% |        24 |
| src/adapters/security/token\_service.py                    |       28 |        3 |     89% |30, 43, 49 |
| src/adapters/user\_repo.py                                 |       45 |       45 |      0% |      1-70 |
| src/api/\_\_init\_\_.py                                    |        0 |        0 |    100% |           |
| src/api/decorators.py                                      |       29 |        2 |     93% |    23, 26 |
| src/api/routes/\_\_init\_\_.py                             |        2 |        0 |    100% |           |
| src/api/routes/auth.py                                     |       84 |       71 |     15% |34-48, 56-164 |
| src/api/routes/errors.py                                   |        9 |        9 |      0% |      1-15 |
| src/api/routes/health.py                                   |       15 |       15 |      0% |      1-21 |
| src/api/routes/notes.py                                    |      126 |       17 |     87% |26-27, 38-41, 48-49, 128, 134, 157, 163, 168, 174, 179, 199, 205 |
| src/api/serializers.py                                     |        4 |        0 |    100% |           |
| src/app.py                                                 |        6 |        6 |      0% |       1-9 |
| src/app\_factory.py                                        |       34 |       34 |      0% |      1-67 |
| src/bootstrap.py                                           |       20 |       20 |      0% |      1-41 |
| src/db.py                                                  |        6 |        6 |      0% |       1-9 |
| src/domain/\_\_init\_\_.py                                 |        3 |        0 |    100% |           |
| src/domain/notes.py                                        |      106 |        1 |     99% |       201 |
| src/domain/notes\_errors.py                                |        5 |        0 |    100% |           |
| src/domain/roles.py                                        |        4 |        0 |    100% |           |
| src/domain/user.py                                         |       43 |       12 |     72% |23, 26, 35, 38, 48-51, 54, 68-71, 74 |
| src/domain/user\_errors.py                                 |        2 |        0 |    100% |           |
| src/environment.py                                         |       20 |        6 |     70% |     30-40 |
| src/service/\_\_init\_\_.py                                |        0 |        0 |    100% |           |
| src/service/uow.py                                         |       41 |        4 |     90% |32, 36, 40, 70 |
| **TOTAL**                                                  |  **944** |  **315** | **67%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/duly-app/duly-backend/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/duly-app/duly-backend/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/duly-app/duly-backend/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/duly-app/duly-backend/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fduly-app%2Fduly-backend%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/duly-app/duly-backend/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.