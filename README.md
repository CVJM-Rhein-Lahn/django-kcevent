# CVJM Card

Python library to fetch addresses and statistics from cvjm-card.de (CVJM Westbund e.V.)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

In order to use the library, you need credentials for the cvjm-card.de side. Only regional chapter logins will succeed right now, as the DOM is parsed.

Beside of this, you need to install some python requirements:

```
python -m pip install -r requirements.txt
```

### Installing

Standard way to install packages. Either manual way:

```
python setup.py build && python setup.py install
```

or pip way (not sure, if this package will be on pip):

```
python -m pip install python-cvjmcard
```

If you've credentials of your regional club, check the example (only manual way):

```
python cvjmcard/client.py
```

After installing, you can access the package via 

```
> from cvjmcard import client
```

## Contributing

You're contribution is appreciated. Create an issue or make a pull-request.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/monofox/python-cvjmcard/tags). 

## Authors

* **Lukas Schreiner** - *Initial work* - [monofox](https://github.com/monofox)

## License

This project is licensed under the GPLv3+ License - see the [LICENSE.md](LICENSE.md) file for details
