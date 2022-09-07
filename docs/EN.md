# Marian NMT training tools and API service

[Darllenwch y ddogfen yma yn Saesneg](docs/EN.md)

This project contains code, scripts and documentation which enables you to host your own [Marian NMT][1] local machine translation system.

To run a local machine translation (MT) service successfully, you will need a computer with a [supported NVIDIA graphics card][14] as well as software packages such as Docker and Python.

The MT system uses translation models that have been specially trained by the Language Technologies Unit for translating from English to Welsh.

There are two methods of using machine translation with this project. The first, through a local API service, that provides the ability to integrate with translation tools (if the software allows). The second, through a website that is also publicly available at [cyfieithu.techiaith.cymru][5].


## Getting started: building your own translation API service

The requirements are the same and should work for all types of computer. 
A slight difference exists depending on which subsystems within Windows 10 you are using.

### Reqiurements

  * [Python 3 for Mac/Linux and Windows WSL2](https://www.python.org/download) / [Python 3 for Windows 10 using Powershell](https://www.microsoft.com/store/productId/9PJPW5LDXLZ5)

  * Docker (Linux / [Mac][10] / [Windows][9])

  * docker-compose ([Linux][8], [Mac a Windows][7])


#### Install steps:

1. Create a new folder

2. Download the [getting-started script][6] into the new empty folder.

3. Open a command prompt (Either `cmd` or `powershell`) with
   *administrator privileges* (i.e choose 'Run as administrator' when opening `cmd` or `powershell`). Move to the new folder where the script was placed. Then run:

```powershell
python techiaith_docker_marian_nmt.py --install --run
```

#### Help

Run the following command within your command line program to see all the available options:

```powershell
python python techiaith_docker_marian_nmt.py --help
```

### Testing

After running the script above, visit:

http://127.0.0.1:8000/api/docs


After pushing the `Try it out` button, the `JSON` text will be shown
in an editable textarea:

```json
{
  "text": "I have a headache.",
  "source_language": "en",
  "target_language": "cy"
}
```

Push the `Execute` button; Results will be shown below the form.

You can experiment with other English by changing the sentence 'I have
a headache' in JSON.

Note that the `curl` command used to perform the example request is shown
in the form; this can be copy-and-pasted into your command line,
where you can experiment with translating different phrases.

## Acknowledgements

We thank the Welsh Government for funding this work as part of the Technoleg Cymraeg 2021-22 project.

This software is made freely available under an [MIT license][11].

[1]: https://marian-nmt.github.io/
[2]: https://hub.docker.com/r/techiaith/docker-marian-nmt-api
[3]: https://hub.docker.com/r/techiaith/docker-marian-nmt-lab
[4]: https://github.com/mjpost/sacrebleu
[5]: https://cyfieithu.techiaith.cymru
[6]: https://raw.githubusercontent.com/techiaith/docker-marian-nmt/v22.09/getting-started/techiaith_docker_marian_nmt.py
[7]: https://docs.docker.com/compose/cli-command/#install-on-mac-and-windows
[8]: https://docs.docker.com/compose/cli-command/#install-on-linux
[9]: https://docs.docker.com/desktop/windows/install/
[10]: https://docs.docker.com/desktop/mac/install/
[11]: https://opensource.org/licenses/MTI
[12]: https://www.microsoft.com/store/productId/9PJPW5LDXLZ5
[13]: https://www.python.org/
[14]: https://en.wikipedia.org/wiki/CUDA#GPUs_supported
