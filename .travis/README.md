# release_tag.sh

This script is run by Travis after the current commit passes all the tests.
It creates the following tags and pushes them to the repo:

- `release_<travis build number>`
- `release`

This requires a GitHub token with permission to write to the repo.

## Testing locally

To test locally we need to fake the environment variables provided by Travis.

Do this by setting `LOCAL_TEST_MODE` to `true` and `TESTING_GITHUB_TOKEN` to a
token you create on GitHub with the `public_repo` permission.

## Running on Travis

When running in Travis the `GH_TOKEN` variable is set by decrypting the `secure` section from the `/.travis.yml` file

To set up a new token, follow these steps:

- Create a new token in GitHub with the `public_repo` permission (preferably as the @gds-ci-pp user)
- Then, in the directory for this application, run:
    - `gem install travis`
    - `travis encrypt --add GH_TOKEN=the-token-from-github`

## Handy links

- [Docs on Travis encrypted environment variables](http://docs.travis-ci.com/user/encryption-keys/)
- [Get the public key of this repo](https://api.travis-ci.org/repos/alphagov/performanceplatform-admin/key)
- [Travis environment variables](http://docs.travis-ci.com/user/ci-environment/)
- [A similar example of working with GitHub and Travis](http://benlimmer.com/2013/12/26/automatically-publish-javadoc-to-gh-pages-with-travis-ci/)
