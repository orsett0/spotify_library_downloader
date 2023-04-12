# Spotify Library Downloader

## What you need

- ### Python3

You need to have Python3 installed to make use of this program.

You'll also need to install the modules `loguru` and `click`.

- ### Node.js

This is necessary to run Freyr-js and download your music.

You can install it from their [home page](https://nodejs.org/en/download/) or using [nvm](https://github.com/nvm-sh/nvm) (which is recommended from Freyr-js author).

- ### AtomicParsley

Another dependency for Freyr-js. You can download it from their [Github page](https://github.com/wez/atomicparsley/releases/latest) or from your package manager.

If you download it manually, make sure to put it in the PATH or use the `--atomic-parsley` command line option.

## TO-DO List

- **Improve the output**
  - Insert a progress bar that shows the progress of the artists
  - Dump all the output from logger and freyr and all the data structure to a log file
  - List the items for which the program was unable to get a uri in a nicer way
- **Add documentation**
- **Add a license**
- **Automatically analyze the user's profile using APIs**
- **Add option to download artists mix and all the songs.**
- **Add option to use absolute or relative path in playlist files**
- **Selecting an output directory should be mandatory.**
- **Make an installation script**

## License

This project uses the following programs:
- freyr-js, from https://github.com/miraclx/freyr-js, licensed under the Apache License 2.0, Miraculous Owonubi (@miraclx) <omiraculous@gmail.com>
- filenamify-cli, from https://github.com/sindresorhus/filenamify-cli, licensed under the MIT License, Sindre Sorhus (https://sindresorhus.com) <sindresorhus@gmail.com>
