# 1 Docker/Linux commands

1. create new dir 

    `mkdir $FOLDER_NAME`

    `cd $FOLDER_NAME`

    - to change the group permissions of a folder in Linux
        `chmod g+rwx $FOLDER_NAME`

    - this can apply to all files and subdir within the folder 
        `chmod -R g+rwx $FOLDER_NAME`

2. download the docker-compose file

    `curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml`

3. pull the freqtrade image

    `docker compose pull`

4. create user directory folder

    `docker compose run --rm freqtrade create-userdir --userdir user_data`

- this command can run the default commands written in the docker-compose file

    `docker compose up -d`

- the database is located at `user_data/tradesv3.sqlite`

# 2 Creating files

This is the trader for live/paper trading the well-developed strategy, mostly using the freqtrade:stable image.

1. create new config

    `docker compose run --rm freqtrade new-config --config user_data/config.json`

2. create new strategy

3. 

# 3 Backtesting

1. download data

    `docker compose run --rm freqtrade download-data --config user_data/config.json --exchange binance --timerange 20230101-20240501 -t 1m 5m 15m 1h`

2. backtest strategy

    `docker compose run --rm freqtrade backtesting --config user_data/config.json --strategy MeanReversionStrategy --timerange 20230101-20240501 -i 15m`

3. plot dataframe
    
    `docker compose run --rm freqtrade plot-dataframe --strategy MeanReversionStrategy -p SUI/USDT:USDT --timerange=20230101-20240501 -i 15m`

    Make sure the image you pull in docker-compose file is the right version 
    (e.g. `freqtradeorg/freqtrade:develop_plot`)

4. analyze data

    `docker compose -f docker/docker-compose-jupyter.yml up`

    - Since part of this image is built on your machine, it is recommended to rebuild the image from time to time to keep freqtrade (and dependencies) up-to-date.

        `docker compose -f docker/docker-compose-jupyter.yml build --no-cache`

5. hyperopt

    `docker compose run --rm freqtrade hyperopt --hyperopt-loss SharpeHyperOptLossDaily --spaces buy roi stoploss trailing --strategy MeanReversionStrategy --config user_data/config.json -i 15m -e 500`

    - You can list past hyperopt results by

        `docker compose run --rm freqtrade hyperopt-list --hyperopt-filename strategy_MeanReversionStrategy_2024-05-08_12-13-57.fthypt`

        and the arguments can be found in [Utility Sub-commands](https://www.freqtrade.io/en/stable/utils/#list-hyperopt-results)