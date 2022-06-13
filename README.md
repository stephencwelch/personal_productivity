## Personal Productivity

### Installation
```
sudo apt-get install texlive texlive-latex-extra pandoc
sudo apt-get install texline-xetex texlive-fonts-recommended texlive-plain-generic
pip3 install -r requirements.txt
```
### Other Setup
- Tab Reloader Firefox add on by James Fray

```
jupyter nbconvert --to script nbs/airtable_tools_v2.ipynb
```

### Cron Job
```
*/10 * * * * python3 /home/stephen/personal_productivity/nbs/airtable_tools_v2.py >> /tmp/personal_productivity_script.log 2>&1
```
```
tail /tmp/personal_productivity_script.log -f
```

### Conventions
