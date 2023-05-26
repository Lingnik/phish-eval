# phishing URL eval for LLMs

An LLM eval for detecting real-world phishing URLs.

## Dataset

`online_valid_2023_05_06_15_55_12.csv`

The included dataset is derived from publicly-available data retrieved from
http://data.phishtank.com/data/online-valid.csv.gz on 2023-05-06T15:55:12Z.
At the time of retrieval, it was subject to Cisco Technologies EULA labeled
`EDM-122989354 Ver: 6.0 Last Modified: Mon Jul 11 21:55:21 PDT 2022`.

The dataset was frozen at that time to ensure repeatable results for an LLM
with a fixed knowledge window. If the LLM is updated, a live dataset should
be retrieved by running `python3 phish_eval.py download`.

To generate the dataset, we filter by:
* "target" != "Other"
* "verified" == "yes"

The columns included were:
* "phish_id" - the ID of the phishing site, for reference
* "url" - the URL of the phishing site, to be evaluated by the LLM
* "target" - the organization the phishing link purportedly impersonates

## Methodology

The premise of this eval is that an LLM can evaluate a URL and impersonated
organization name, and determine whether the URL is a phishing link. We use
a one-shot prompt with no prior turns, to avoid nondeterministic results as
a result of the LLM's reasoning or past evaluations biasing the result each
time we generate a completion. By purporting to be a victim, the LLM should
be unlikely to enter a failsafe (moderated) mode where it refuses to answer
the prompt. Lastly, we request a fixed output format to make validating the
results easier.

The prompt we use is:

    I received an email from {{source}} with a link to: `{{url}}`
    
    Answer the question: Is this a phishing email?
    
    Please respond in JSON like `TRUE` or `FALSE`, without a code block.

