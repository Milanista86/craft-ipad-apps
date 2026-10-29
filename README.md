# PhotoCraft, WordCraft & PdfCraft — Native iPadOS App Wrapper

This folder contains everything needed to build **PhotoCraft**, **WordCraft**, and **PdfCraft** into three standalone **`.ipa` iPad apps** (`PhotoCraft-iPad.ipa`, `WordCraft-iPad.ipa`, and `PdfCraft-iPad.ipa`) for your **iPad Pro M1** — **without needing a Mac**.

---

## How It Works (In Plain English)

1. **GitHub's Free Cloud Mac Builds the Apps for You:**
   Because Apple only allows building `.ipa` apps on macOS, this folder includes an automated workflow ([`.github/workflows/build-ipad-apps.yml`](.github/workflows/build-ipad-apps.yml)). When you upload this folder to your own GitHub account, GitHub spins up a free Mac in the cloud, grabs the latest WebAssembly engine of **PhotoCraft**, **WordCraft**, and **PdfCraft** from `storytold`, wraps each one inside our native Swift iPadOS app ([`ios-wrapper/`](ios-wrapper/)), and gives you 3 `.ipa` files to download.
2. **100% Offline Desktop Engine on Your iPad Pro M1:**
   Inside each `.ipa` app is an embedded localhost server ([`LocalAssetServer.swift`](ios-wrapper/Sources/LocalAssetServer.swift)) and a full-screen desktop view ([`CraftWebViewController.swift`](ios-wrapper/Sources/CraftWebViewController.swift)).
   - **Opening files:** Works directly with the native **iPadOS Files app**.
   - **Saving files (`.psd`, `.docx`, `.pdf`):** Automatically pops up the native iPadOS **"Save to Files"** sheet.
   - **Touch & Apple Pencil Helper:** Includes a small `⚙️` button in the bottom-right corner so you can toggle **Right-Click** or open the **On-Screen Keyboard** when you aren't using a physical keyboard/mouse.

---

## Step-by-Step Instructions (On Your Windows PC)

### Step 1: Create an Empty Repository on GitHub
1. Open [https://github.com/new](https://github.com/new) in your browser and sign in.
2. Under **Repository name**, type `craft-ipad-apps`.
3. Leave everything else as default (do **not** check "Add a README file") and click **Create repository**.
4. Copy the URL shown on the screen (it looks like `https://github.com/YOUR-USERNAME/craft-ipad-apps.git`).

### Step 2: Upload This Folder to GitHub
1. Open your `For iPad` folder on your Desktop (`c:\Users\farou\Desktop\For iPad`).
2. Double-click **`push-to-github.bat`**.
3. Paste the GitHub URL you copied in Step 1 and press **Enter**.
   *(Or simply paste the URL in our chat and I will push it for you automatically!)*

### Step 3: Download Your 3 `.ipa` Files from GitHub
1. Go back to your GitHub repository page in your browser and click the **Actions** tab at the top.
2. Click on the running workflow called **Build iPadOS Apps (.ipa)**.
3. Once all three green checkmarks appear (`Build PhotoCraft (.ipa)`, `Build WordCraft (.ipa)`, `Build PdfCraft (.ipa)`), scroll down to the **Artifacts** section at the bottom of that page.
4. Click to download:
   - **`PhotoCraft-iPad-IPA`** (unzip it to get `PhotoCraft-iPad.ipa`)
   - **`WordCraft-iPad-IPA`** (unzip it to get `WordCraft-iPad.ipa`)
   - **`PdfCraft-iPad-IPA`** (unzip it to get `PdfCraft-iPad.ipa`)

### Step 4: Install the `.ipa` Files Onto Your iPad Pro M1 from Windows
1. Download and install **[Sideloadly](https://sideloadly.io/)** on your Windows PC (it is the standard tool for signing and installing `.ipa` files on Windows using your Apple Developer account).
   *(Make sure you also have the standard Windows versions of **iTunes** and **iCloud** installed—not the Microsoft Store versions—so Windows can talk to your iPad).*
2. Plug your **iPad Pro M1** into your Windows PC with a USB-C cable (and tap **Trust This Computer** on your iPad if asked).
3. Open **Sideloadly**:
   - Enter your **Apple ID** (your Apple Developer account email).
   - Drag **`PhotoCraft-iPad.ipa`** into the `.ipa` box on the left.
   - Click **Start** (enter your Apple ID password on first use).
4. Repeat the drag-and-click for **`WordCraft-iPad.ipa`** and **`PdfCraft-iPad.ipa`**.
   Because each app has its own unique Bundle ID (`com.craftsuite.photocraft`, `com.craftsuite.wordcraft`, `com.craftsuite.pdfcraft`), all three will install side-by-side on your iPad Home Screen!
