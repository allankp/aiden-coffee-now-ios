# Coffee Now ☕

Trigger your Fellow Aiden coffee maker to start brewing via GitHub Actions.

## Setup

### 1. Clone & Create Private Repo

```bash
# Clone the repo
git clone https://github.com/ORIGINAL_OWNER/aiden-coffee-now-ios.git
cd aiden-coffee-now-ios

# Create your own private repo
gh repo create coffee-now --private --source=. --push
```

### 2. Add GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|-------------|-------|
| `FELLOW_EMAIL` | Your Fellow account email |
| `FELLOW_PASSWORD` | Your Fellow account password |

### 3. Populate Your Profiles

Run the List Profiles workflow to fetch your Aiden profiles:

```bash
gh workflow run "List Profiles"
```

This will update the README with your available profiles (runs automatically every Sunday).

### 4. Test It

```bash
gh workflow run "Make Coffee" -f profile_name="YOUR_PROFILE_NAME"
```

## Available Profiles

<!-- PROFILES:START -->
<!-- AUTO-GENERATED - DO NOT EDIT -->
| Profile | ID |
|---------|-----|
| (Run "List Profiles" workflow to populate) | - |
<!-- PROFILES:END -->

## Usage

### Make Coffee

```bash
gh workflow run "Make Coffee"
```

With options:

```bash
gh workflow run "Make Coffee" \
  -f profile_name="Default" \
  -f water_amount=500 \
  -f delay_minutes=6
```

### List Profiles

```bash
gh workflow run "List Profiles"
```

## iOS Shortcut Setup

Trigger coffee brewing from your iPhone with Siri or a home screen button.

### 1. Create a GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens?type=beta) → **Fine-grained tokens**
2. Click **Generate new token**
3. Name it "Coffee Shortcut"
4. Under **Repository access** → **Only select repositories** → select this repo
5. Under **Permissions** → **Repository permissions**:
   - **Actions**: Read and write
   - **Contents**: Read-only
6. Click **Generate token** and copy it

### 2. Create the Shortcut

1. Open **Shortcuts** app → tap **+**
2. Add **Get Contents of URL** action:
   - **URL**: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/make-coffee.yml/dispatches`
   - **Method**: POST
   - **Headers**:
     - `Authorization`: `Bearer YOUR_TOKEN_HERE`
     - `Accept`: `application/vnd.github.v3+json`
   - **Request Body**: JSON
     ```json
     {
       "ref": "main",
       "inputs": {
         "profile_name": "Default",
         "water_amount": "500",
         "delay_minutes": "6"
       }
     }
     ```
3. Add **Show Notification** → "☕ Coffee brewing!"
4. Name it "Make Coffee"

### 3. Optional: Add Profile Selection

To choose a profile each time:

1. Add **Choose from Menu** action at the top with your profile names
2. For each option, set a **Text** action with the profile name
3. Use that variable in the JSON body for `profile_name`

### 4. Trigger It

- **Siri**: "Hey Siri, Make Coffee"
- **Home Screen**: Long-press shortcut → Add to Home Screen
- **Lock Screen**: Add as a widget (iOS 16+)

## Credits

Built using [fellow-aiden](https://github.com/9b/fellow-aiden) by [Brandon Dixon (9b)](https://github.com/9b)
