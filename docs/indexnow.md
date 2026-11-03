# IndexNow

[IndexNow](https://www.indexnow.org/) tells participating search engines that
URLs on the site changed, so they recrawl sooner instead of waiting for the
sitemap to be picked up.

- Key file: `/21cb1773dbcb22af14e0fadaf5e8c085.txt` at the site root. It holds
  only the key and is public by design: IndexNow fetches it to confirm that
  pings for `manajev.com` come from the site owner.
- Script: `scripts/indexnow-ping.py` (Python 3, standard library only). It reads
  every `<loc>` from `sitemap.xml` and POSTs them to
  `https://api.indexnow.org/indexnow` with the host, key and key location.
- `docs/` and `scripts/` are excluded from the published site in `_config.yml`.

## After a GitHub Pages deploy

1. Wait for the Pages build of `master` to finish:

   ```sh
   gh api repos/legalaspro/legalaspro.github.io/pages/builds/latest --jq .status
   ```

   It should print `built`.

2. From an up-to-date checkout of `master`, preview the request:

   ```sh
   python3 scripts/indexnow-ping.py --dry-run
   ```

3. Send it:

   ```sh
   python3 scripts/indexnow-ping.py
   ```

   The script first checks that the live key file returns the key, then POSTs.
   `HTTP 200` or `HTTP 202` means the URLs were accepted (202: the key is still
   being verified). Any other response, or a network error, prints the reason
   and exits with status 1. Common ones: 403 (key file not reachable or wrong),
   422 (a URL is not on `manajev.com`), 429 (too many requests; try later).

Ping only when pages actually changed; re-sending unchanged URLs gains nothing.
Options: `--sitemap PATH` reads a different sitemap, `--endpoint URL` posts to
another IndexNow endpoint.

## Rotating the key

Delete the old key file and add a new `<32 hex chars>.txt` at the site root
that contains only its own name:

```sh
key=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
printf '%s' "$key" > "$key.txt"
```

Update the file name above and deploy before the next ping. The script finds
the key file on its own.
