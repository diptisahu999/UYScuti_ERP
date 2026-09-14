FROM odoo:19.0

USER root

# Install any custom system requirements if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# If you have custom python packages, uncomment the lines below:
# COPY requirements.txt /etc/odoo/requirements.txt
# RUN pip3 install -r /etc/odoo/requirements.txt
# Install custom python packages
RUN pip3 install qifparse pypdf --break-system-packages

USER odoo
