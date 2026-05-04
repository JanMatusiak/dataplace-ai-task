# My journal of working on this project

### 30.04.2026 - 1 hour
**Done**:
- Set up the project, .env_example, .env, .venv and requirements.txt via `pip freeze > ...`
- Used `load_dotenv` for the first time to automatically read environment variables
- Connected to AWS S3 and Snowflake using Python libraries `boto3` and `snowflake-connector-python`

**Insights**:
- S3 is a cloud storage service offered by Amazon Web Services. It uses buckets (folders) for storing objects (files).
- Snowflake is cloud data warehouse, and an alternative to BigQuery and Redshift. It separates compute and storage and can
handle terabytes of data in seconds. Requires opening a connection with credentials and creating a cursor to send SQL queries.
- `python-dotenv` is an open-source package that reads your environment variables and allows you to call them from `os.getenv()`
- pip provides a lot of interesting methods to inspect details and dependencies between packages, 
for instance `pip show <package_name>`
- `pip freeze > requirements.txt` saves the currently used versions of packages in your local interpreter into `requirements.txt`,
providing a uniform source-of-truth when it comes to package version used in the project
- Error messages can be misleading — `pandas not installed` actually meant something else (the package was installed without [pandas] extras). 
Lesson: when debugging, always verify what the package itself thinks is installed via pip show, not just whether you can import something.
- I spent some time debugging why I cannot call `cursor.fetch_pandas_all()` despite installing `snowflake-connector-python[pandas]`
as per instruction in Snowflake documentation. [extras] syntax in pip (like package[extra1,extra2]) installs optional dependency groups. 
If you install the package first without extras, then add them later, pip thinks the package is already installed and doesn't add the 
extras — `--force-reinstall` fixes this. 

**Decisions made**:
- I decided to use /notebooks for exploration and analysis and /src for reusable code parts and stable infrastructure
- I decided not to filter `requirements.txt` for packages used in this project only. Right now, it includes some packages
inherited from other projects I worked on before I learned to use `.venv`. 


### 3.05.2026 - 2 hours
**Done:**
- Inspected the `.csv` files with locations, competitors, POIs, analyzed area and districts
- Performed EDA of the data, identified outliers for monthly revenue and out-of-bounds locations
- Sketched an initial map of all locations

**Insights:**
- `geopandas` and `shapely` provide amazing tools for spatial data analysis, while `folium` makes it very easy to create 
interactive, layered maps. I parsed WKT polygons and created points from lng/lat. 

**Decisions made:**
- Analysis bbox will be saved in a JSON format for reference.
- A map of locations will be built and updated for consecutive layers of data (analyzed area, districts, locations etc.)
- Keep all revenue outliers
- All point geometries in EPSG:4326


### 4.05.2026 - 4 hours
**Done**
- Built a layered map from objects identified in local `.csv` files
- Inspected the data from AWS S3, identified distributions, asserted certain relationships
- Started inspecting the data from Snowflake, inspected the number of rows from our analysis area

**Insights:**
- There were several statistical outliers in multiple analyzed columns, however, they are all kept based on the context. 
- The distributions of numerical values were right-skewed.
I still have to mind that actual outliers can be present and should be handled one way or another.
- The bbox of analysis area and district union area is exactly the same. However, district union still covers a larger area.

**Decisions made**
- Analysis area will be used for whitespot analysis, however, client already has stores outside this area - they will be
used when developing model. This decision was made after consulting the Head of Data.