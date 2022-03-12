# Marian NMT training tools and API service

This project contains code, scripts and documentation which enables
you to create your own [Marian NMT][1] machine translation
system.

If you have docker installed and running on your system, then it's
easy get started by installing with one of the docker images provided:

1. [Marian NMT API service][2]

   * Providing:

      + API endpoints for translating English -> Welsh.

      + Interactive API documentation.

2. [Marian NMT Lab][3]

    *  Providing:

       + Management of Marian training sessions.

       + Running of Marian training tasks.

       + Downloading data.

       + Cleaning and exporting the data.

       + Creating training sets for use with Marian.

       + Running Marian tranining.

       + Evaluation of the results via scoring (with [SacreBLEU][4]).

An example web inteface is also included in this repository under the `frontend` directory,
publicly available and running at [cyfithiethu.techiaith.cymru][5].


## Getting started: building your own translation API service

The easiest way to use this software is via our pre-built docker images above.

If you've already got docker installed on your computer, then after
downloading and running a Python script as detailed below, then you
will be up and running!

By default the script will:
 - Create a subdirectory in your home directory: `techiaith-docker-marian-nmt`
 - A model will be downloaded to a sub-directory therein.
 - The docker image will be downloaded to run locally on your computer.
 - The web API service will start, and a message printed to confirm it's running.


### On Windows 10 with [Docker Desktop][9]

* Reqiurements:

  * [Python][12]

  * [Docker][9] :information_source: [Enable docker compose v2][7].


1. [Download][6] the getting-started script.

2. Open a command prompt (Either `cmd` or `powershell`) with
   *administrator privileges* and run the script:

```powershell
python techiaith_docker_marian_nmt.py
```

### Linux / MacOSX / Windows10 WSL2

* Reqiurements:

  * [Python][13]

  * Docker (Linux / [Mac][10] / [Windows][9])
	:information_source: [Enable docker compose v2][8]


[Download][6] the getting-started script and run:

```bash
python techiaith_docker_marian_nmt.py
```

This software is made freely available under an [MIT license][11].

We thank the Welsh Government for funding this work as part of the
Technoleg Cymraeg 2021-22 project.

[1]: https://marian-nmt.github.io/
[2]: https://hub.docker.com/r/techiaith/docker-marian-nmt-api
[3]: https://hub.docker.com/r/techiaith/docker-marian-nmt-lab
[4]: https://github.com/mjpost/sacrebleu
[5]: https://cyfeithu.techiaith.cymru
[6]: https://raw.githubusercontent.com/techiaith/docker-marian-nmt/v22.03/getting-started/techiaith_docker_marian_nmt.py
[7]: https://docs.docker.com/compose/cli-command/#install-on-mac-and-windows
[8]: https://docs.docker.com/compose/cli-command/#install-on-linux
[9]: https://docs.docker.com/desktop/windows/install/
[10]: https://docs.docker.com/desktop/mac/install/
[11]: https://opensource.org/licenses/MTI
[12]: https://www.microsoft.com/store/productId/9PJPW5LDXLZ5
[13]: https://www.python.org/
