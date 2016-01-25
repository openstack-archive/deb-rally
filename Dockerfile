FROM ubuntu:14.04
MAINTAINER Sergey Skripnick <sskripnick@mirantis.com>

# install prereqs
RUN apt-get update && apt-get install --yes wget python

# ubuntu's pip is too old to work with the version of requests we
# require, so get pip with get-pip.py
RUN wget https://bootstrap.pypa.io/get-pip.py && \
  python get-pip.py && \
  rm -f get-pip.py

# create rally user
RUN useradd -u 65500 -m rally && \
  ln -s /opt/rally/doc /home/rally/rally-docs

# install rally. the COPY command below frequently invalidates
# subsequent cache
COPY . /tmp/rally
WORKDIR /tmp/rally
RUN ./install_rally.sh --system --verbose --yes \
    --db-name /home/rally/.rally.sqlite && \
  pip install -r optional-requirements.txt && \
  mkdir /opt/rally/ && \
  mv certification/ samples/ doc/ /opt/rally/ && \
  chmod -R u=rwX,go=rX /opt/rally /etc/rally && \
  rm -rf /tmp/* && \
  apt-get -y remove \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    python3 \
  && \
  apt-get -y autoremove && \
  apt-get clean

RUN echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/motd' \
            >> /etc/bash.bashrc; echo -e 'Welcome to Rally Docker container!\n\
    Rally certification tasks, samples and docs are located at /opt/rally/\n\
    Rally at readthedocs - http://rally.readthedocs.org\n\
    How to contribute - http://rally.readthedocs.org/en/latest/contribute.html\n\
    If you have any questions, you can reach the Rally team by:\n\
      * e-mail - openstack-dev@lists.openstack.org with tag [Rally] in subject\n\
      * irc - "#openstack-rally" channel at freenode.net' > /etc/motd

VOLUME ["/home/rally"]

WORKDIR /home/rally/
USER rally
ENV HOME /home/rally/
CMD ["bash", "--login"]

RUN rally-manage db recreate

# TODO(stpierre): Find a way to use `rally` as the
# entrypoint. Currently this is complicated by the need to run
# rally-manage to create the database.
