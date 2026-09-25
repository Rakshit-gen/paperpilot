from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
def invoke_with_retry(chain, inputs: dict):
    """Retry a Groq call up to 3 times with exponential backoff.

    Groq's client doesn't cleanly distinguish a transient error (rate
    limit, timeout) from a permanent one, so this retries on any
    exception. The one permanent failure we know about ahead of time, a
    missing API key, is caught by require_groq_key() before this ever
    runs, so it still fails immediately instead of retrying.
    """
    return chain.invoke(inputs)
