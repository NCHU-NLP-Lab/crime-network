# Data Processing

- Download dataset from [Google Drive](https://drive.google.com/drive/folders/1t6fFUE45dhDPdNkm5Yg2BgPFqt7HoE_E?usp=sharing)
- Run `dump_verdict.py` to load raw data into MongoDB, then run `build_relationships.py` to construct graph in database.
- Make sure to fill the proper environment variable before running.
- The old version `dump_verdict.py` are slow due to large amount of jsons being open/close back and forth and inserted one-by-one
- Use the experimental `convert.sh` can convert json data into jsonl format
- Modifying the `dump_verdict.py` to load with jsonl format should have significant performance boost

