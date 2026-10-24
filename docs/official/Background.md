# Background

(name=Background, mime=None, published=None)

**What is an MS/MS mass spectrum?**

You don't need a chemistry background to compete, but it helps to understand the basics of how mass spectra are generated in a mass spectrometer:

- **Ionization:** The instrument can only detect and measure charged ions, so first a molecule is ionized, picking up or losing charged species. In the instrument’s **positive ion mode** (more common for small molecules), the resulting ion is positively charged, in **negative ion mode** (less common but still used), it is negatively charged. The kind of charged ion the molecule acquires is called an adduct.  For some common examples, the molecule may acquire a proton (positive), acquire an ammonium ion (positive), or lose a proton (negative). We would write these **adduct** forms respectively as [M+H]+, [M+NH4]+, or [M-H]-.

- **Precursor mass detection:** The instrument measures the ion's **precursor m/z** (mass-to-charge ratio) with high accuracy, which strongly constrains the molecular formula. For small molecules, the charge (z) is usually +1 or -1, so m/z corresponds to the mass of the ion, and sometimes we will refer to m/z simply as “mass”.

- **Fragmentation:** The precursor ion (actually many individual ions of the same molecule+adduct) is then selected and fragmented by collision with neutral gas at a given **collision energy,** and the instrument records the **m/z and intensity (abundance) of each fragment**. The histogram of intensities across all detected fragments is the molecule’s mass spectrum. Intensities are typically normalized. A mass spectrum looks like this:

<img src="https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F8939556%2Ff963c879de099c80f7e42cc3f1605f63%2FScreenshot%202026-09-10%20at%2010.32.21AM.png?generation=1789061564592295&alt=media" style="max-width:75%;margin-left: auto;margin-right: auto;display: flex;" alt="MS/MS spectrum of Chrysin">

Figure 1: MS/MS spectrum of Chrysin [M-H]- adduct at around 50eV, timsTOF (Source: Enveda)

Each m/z is called a **fragment ion or peak**. The **base peak** is the highest-intensity fragment ion. The **precursor peak** is the m/z corresponding to the intact, unfragmented ion. It may or may not be present, depending on how thoroughly the ion was fragmented.