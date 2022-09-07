# Offer hyfforddi Marian NMT a gwasanaeth API

[Read in English](docs/EN.md)

Mae'r project hwn yn cynnwys popeth sydd ei hangen i redeg peiriant cyfieithu peirianyddol niwral [Marian NMT][1] lleol eich hunan.Mae'r feddalwedd i gyd yn god agored ac ar gael o dan delerau'r drwydded [MIT][11].

I redeg cyfieithu peirianyddol lleol yn llwyddiannus, byddwch angen cyfrifiadur â [cherdyn graffeg NVIDIA][14] yn ogystal â phecynnau meddalwedd fel Docker a Python wedi'u osod yn barod.

Mae'r peiriant yn defnyddio modelau cyfieithu sydd wedi'u hyfforddi'n arbennig gan yr Uned Technolegau Iaith i gyfieithu o Saesneg i'r Gymraeg. 

Darparir dwy ddull o ddefnyddio'r cyfieithu peirianyddol gan y project. Y gyntaf, drwy wasanaeth API lleol, sydd yn galluogi integreiddio i offer cyfieithu (os yw'r meddalwedd yn caniatau). Yr ail, drwy dudalen we syml sydd yn rhedeg yn gyhoeddus a [cyfieithu.techiaith.cymru][5].


## Cychwyn arni: rhedeg gwasanaeth API cyfieithu peirianyddol lleol eich hunain

Yr un prif ofynion sydd eu hangen i bob math o gyfrifiadur. Ond mae amrywiadau bychain yn ôl ba fath o gyfrifiadur Windows 10 rydych yn bwriadu defnyddio.

#### Gofynion:

  * [Python 3 i Mac/Linux a Windows WSL2](https://www.python.org/download) / [Python 3 i Windows 10 o fewn Powershell](https://www.microsoft.com/store/productId/9PJPW5LDXLZ5)

  * Docker (Linux / [Mac][10] / [Windows][9])

  * docker-compose ([Linux][8], [Mac a Windows][7])

#### Camau gosod:

1. Crëwch ffolder newydd

2. Lawrlwythwch y [sgript gosod a chychwyn arni][6] a'i chadw o fewn y ffolder gwag newydd

3. Agorwch raglen gorchymyn llinell (e.e 'Terminal`, `cmd` neu `Powershell`) gyda *breintiau gweinyddwr* (h.y. dewiswch 'Rhedeg fel Gweinyddwr'/'Run as Administrator'). Ewch i'r ffolder newydd lle cadwyd y sgript gosod. Yna, weithredwch drwy :

```powershell
python techiaith_docker_marian_nmt.py --install --run
```
#### Cymorth

Rhedwch y gorchymyn canlynol o'ch raglen gorchymyn llinell i weld yr holl opsiynau sydd ar gael.

 ```powershell
 python python techiaith_docker_marian_nmt.py --help
 ```
 
### Profi

Ar ol rhedeg y sgript uwchod, ewch i'r dolen:

http://127.0.0.1:8000/api/docs

Wrth gwrthio'r botwn `Try it out`, dangosir testun `JSON` mewn bwlch:

```json
{
  "text": "I have a headache.",
  "source_language": "en",
  "target_language": "cy"
}
```

Gwthiwch y botwm `Execute`; Dangosir y canlyniadau o dan y ffurflen.

Mae modd arbrofi gyda thestunau Saesneg eraill wrth newid y frawddeg
'I have a headache' yn y cod JSON.


Sylwch fod y gorchymyn `curl` i gynhyrchu'r cais enghreifftiol yn cael
ei arddangos yn y ffurflen. Gallwch gopïo a gludo hwn i'ch llinell
orchymyn er mwyn arbrofi ag ef.


## Diolch

Diolch i Lywodraeth Cymru am ariannu'r gwaith hwn fel rhan o broject Technoleg Cymraeg 2021-22.

Mae'r meddalwedd yma wedi roi yw gael am rhydd o dan trwydded [MIT license][11].

[1]: https://marian-nmt.github.io
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
[14]: https://en.wikipedia.org/wiki/CUDA#GPUs_supported
