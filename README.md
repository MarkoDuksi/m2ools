# m2ools

Many implementations of functionalities such as cache and retry already exist, therefore the "me too" on these.

## Description

Main use of these tools is to aid in common web scraping tasks.

### jitter and jitterargs
- `jitter` decorates a function to jitter its numeric return value in a particular way (see 'example_jitter.py')
- `jitterargs` decorates a function to jitter its numeric arguments in a particular way (see 'example_jitter.py')

Most commonly used with jitter factors set to 1 when used for timing delays to assure the jittered value is non-negative. For other purposes one can choose to jitter more or less aggressively:

![Effect of jitterfactor on jitter spread](https://github.com/MarkoDuksi/m2ools/blob/main/images/jitter.png)

Well documented in code.

### retry
Decorates a function to keep calling it until a satisfying return value is obtained. For example retrying a request for a defined maximum number of times with powerful configuration options for variable delays between consecutive calls and a custom function to validate the return value. Well documented in code. See 'example_retry.py'.

### cache
Decorates a function to cache its results to disk. Supports hoarding of results. Useful when developing a web scraper and not wanting to send the same request again and again on each new run. Or simply when hoarding is desired to maintain a history of results as a time series. Supports a flexible format for specifying maximum age of cached results before they go stale. See 'example_cache.py'.

TBD: Would benefit from better documenting this part of code.

## Usage

Best illustrated in 'example_*' files. To preemptively avoid conflicts it is recommended to `import m2ools as m2` and then use `@m2.jitter`, `@m2.retry(reachback='1 hour')`and so forth.

## Authors

Marko Dukši
[@LinkedIn](https://www.linkedin.com/in/mduksi/)

## Version History

- 0.1
    * Initial Release

## License

This project is licensed under the MIT License.
