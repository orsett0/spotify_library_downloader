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
  - Parse freyr output to show failed downloads.
  - Use only one line to show the progress, don't flood the console.
- **Add documentation**
- **Automatically analyze the user's profile using APIs**
- **Add option to download artists mix and all the songs.**
- **Add option to use absolute or relative path in playlist files**
- **Make an installation script**
- **Solve some problems with searching files to populate the playlists**
  - Some albums/traks have different names than what spotify says. (I assume) this can happen when an artist changes the name of an album after the user put the song in a playlist. It can also happen that at some point in time some ascii characters or characters sequence get replaced from an unicode equivalent (example: '-' -> '–', '...' -> '…').
- **Add ability to not overwrite local changes made to playlists**
- **Clear freyr cache at every call**

## License

Copyright (C) 2023 Alessio Orsini <alessiorsini.ao@proton.me>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

This project also uses the following programs:
- freyr-js, from https://github.com/miraclx/freyr-js, licensed under the Apache License 2.0, Miraculous Owonubi (@miraclx) <omiraculous@gmail.com>
- filenamify-cli, from https://github.com/sindresorhus/filenamify-cli, licensed under the MIT License, Sindre Sorhus (https://sindresorhus.com) <sindresorhus@gmail.com>
