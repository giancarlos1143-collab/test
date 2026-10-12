# Getting the app onto your iPhone

Everything runs from one command on your Mac: `python3 -m flowtracker.serve`. It serves the app,
the data, and the scheduled scans. Pick how your phone reaches it.

> Prices below are from memory, not checked live (my build environment couldn't reach those sites).
> Confirm on each site before paying anything.

## Step 1: Same Wi-Fi (free, 5 minutes)
1. On the Mac: `python3 -m flowtracker.serve`. It prints an address like `http://192.168.1.23:8000`.
2. On the iPhone (same Wi-Fi), open **Safari** and type that address.
3. Tap the **Share** button, then **Add to Home Screen**, then **Add**. It now opens full screen with its own icon.
4. If it won't load: Mac System Settings → Network → Firewall → allow incoming connections for Python.

Limits: only works at home, and only while the Mac is awake and running the command.
Keep it awake with `caffeinate -i python3 -m flowtracker.serve`.

## Step 2: Works anywhere. Recommended: Tailscale (free)
Tailscale makes a private network between your devices. Nothing is exposed to the internet, so it is
the safest option, and your Mac is the "server".
1. Create a free account at tailscale.com. Install Tailscale on the Mac and the iPhone (App Store). Sign in with the same account on both.
2. In the Tailscale app on the Mac, note its name (like `macbook`) or its `100.x.y.z` address.
3. On the iPhone, with Tailscale on, open Safari at `http://macbook:8000` (or `http://100.x.y.z:8000`) and Add to Home Screen as above.
4. Optional, for a proper `https://` address: in the Tailscale admin page enable **HTTPS certificates**, then on the Mac run
   `tailscale serve --bg 8000`. Use the `https://…ts.net` address it prints.

Still set `APP_PASSWORD` in `.env` (extra safety). Limits: the Mac must be on, awake and running for scans and access.

## Step 3: Always on (optional, costs money)
Only if you don't want to depend on your Mac. Run the same code on a small cloud machine. Rough costs: a small
VPS (Hetzner, DigitalOcean) around $4-6/month; platforms like Fly.io or Railway around $3-7/month. The app needs
a **persistent disk** (the SQLite file) and a process that stays running; free tiers that sleep or wipe the disk
don't work. If you go this way:
- Set `APP_PASSWORD` to something long. **Never** put the app on the internet without it.
- Put it behind HTTPS (these platforms provide it).
- Copy `data/flow.db` up to keep your history.
I haven't set this up because it costs money. Tell me which provider and I'll prepare the files.
