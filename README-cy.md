# Offer hyfforddi Marian NMT a gwasanaeth API

[Read in English](English)

Mae'r project hwn yn cynnwys cod, sgriptiau a dogfennaeth sy'n eich galluogi chi
i greu peiriant cyfieithu peirianyddol [Marian NMT][1] eich hunan.

Os oes gennych docker wedi'i osod ac yn rhedeg ar eich cyfrifiadur, wedyn mae'n hwylus
i ddechrau mynd ymlaen a gosod un o'r lluniau docker sydd wedi'u darparu:

1. [Marian NMT API service][2]

 * Yn darparu:

  + diweddbwynt API ar gyfer cyfieithu o'r Saseneg i'r Gymraeg.

  + Dogfennaeth API rhyngweithiol.

2. [Marian NMT Lab][3]

 *  Yn darparu modd i weithio gyda Marian er mwyn:

  + Rheoli sesiynau hyfforddi.

  + Rhedeg tasgau rheoli hyfforddi.

  + Lawrlwytho data.

  + Glanhau ac allforio data.

  + Creu setiau testunau hyfforddi.

  + Rhedeg hyfforddiant Marian.

  + Gwerthuso a sgorio canlyniadau o'r sesiynau hyfforddi  (gyda'r offer [SacreBLEU][4]).


Mae enghraifft o ryngwyneb hefyd wedi'i chynnwys yn y storfa yma, o dan y cyfeiriadur `frontend`.
Mae'r wefan ar gael ac yn rhedeg yn gyhoeddus ar [cyfieithu.techiaith.cymru][5].


## "Getting started": adeiladu gwasanaeth "API" cyfieithu peirianyddol eich hunnain

Y ffordd fwyaf hwylus i defnyddio'r meddalwedd yma yw trwy defnyddio
ein "docker" images (wedi ei doleni'i uwchod).

Os rydych yn barod gyda docker wedi osod ar eich cyfriadur, ar ol
lawrlywtho ac rhedeg sgript Python sydd wedi ei manylir isod, byddwch
i fynnu a rhedeg!

Bydd y sgript yn:
 - Creu is-cyferiadur yn eich cyferiadur catref: `techaiith-docker-marian-nmt`
 - Bydd fodel wedi ei lawrlwytrho i is-cyferiadur ty fewn i hynnu.
 - Bydd "docker image" yn cael ei lawrlwytho er mwyn rhedeg yn lleol ar eich cyfrifiadur.
 - Bydd y gwasaneth API we wedi'i ddechrau, ac dylsai neges wedi ei allbwn i'r sgrin
   i gadarnhau fod y gosodiaeth wedi llwyddo.


### Ar Windows 10 gydag [Docker Desktop][9], yn defnyddio PowerShell

* Gofynion:

  * [Python][12]

  * [Docker][9] :information_source: [Galluogi docker compose v2][7].


1. [Lawrlwythwch][6] y script dechreol.

2. Agorwch rhaglen gorchymyn llinell (e.e `cmd` or `powershell`) gyda
   breintiau gweinyddwr ac rhedwch y sgript:

```powershell
python techiaith_docker_marian_nmt.py
```

### Linux / MacOSX / Windows10 WSL2

* Gofynion:

  * [Python][13]

  * Docker (Linux / [Mac][10] / [Windows][9])
    :information_source: [Gallugoi fersiwn docker compose v2][8].


[Lawrlwythwch][6] y script dechreol ac rhedeg:

```bash
python techiaith_docker_marian_nmt.py
```

Mae'r feddalwedd hon wedi rhyddhau gael o dan trwydded agored [MIT][11].

Diolch i Lywodraeth Cymru am ariannu'r gwaith hwn fel rhan o broject
Technoleg Cymraeg 2021-22.

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
