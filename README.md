## Personal Productivity

### Installation
```
sudo apt-get install texlive texlive-latex-extra pandoc
sudo apt-get install texline-xetex texlive-fonts-recommended texlive-plain-generic
pip3 install -r requirements.txt
```
### Other Setup
- Tab Reloader Firefox add on by James Fray

### Cron Job
```
* /10 * * * * jupyter nbconvert --ExecutePreprocessor.timeout=600 --to pdf --execute /home/stephen/personal_productivity/airtable_tools_v2.ipynb 
```


### Conventions
