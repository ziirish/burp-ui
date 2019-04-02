Changelog
=========

0.6.6 (04/02/2019)
------------------

- Fix: python 3.7 compatibility `#304 <https://git.ziirish.me/ziirish/burp-ui/issues/304>`__
- Fix: agent cannot start `#302 <https://git.ziirish.me/ziirish/burp-ui/issues/302>`__

0.6.5 (03/27/2019)
------------------

- Fix: packaging issue

0.6.4 (03/26/2019)
------------------

- Fix: sync pkgs requirements with burp-ui's `#300 <https://git.ziirish.me/ziirish/burp-ui/issues/300>`__

0.6.3 (03/13/2019)
------------------

- Fix: don't preload LDAP users `#270 <https://git.ziirish.me/ziirish/burp-ui/issues/270>`__

0.6.2 (03/05/2019)
------------------

- Fix: wrong command suggestion `#296 <https://git.ziirish.me/ziirish/burp-ui/issues/296>`__
- Fix: allow templates removal `#290 <https://git.ziirish.me/ziirish/burp-ui/issues/290>`__
- Fix: support burp-2.2.16 `#291 <https://git.ziirish.me/ziirish/burp-ui/issues/291>`_
- Fix: issue `#268 <https://git.ziirish.me/ziirish/burp-ui/issues/268>`_

0.6.1 (05/17/2018)
------------------

- Improvement: Don't cache any data when there is a running backup
- Fix: cannot display bui-agent version
- Fix: live-monitor was broken do to a missing cache
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/0.6.0...0.6.1>`__

0.6.0 (05/14/2018)
------------------

- **BREAKING**: the *BASIC* ``ACL`` engine will now grant users on all agents if they are not explicitly defined
- **BREAKING**: a new ``[ACL]`` section has been created in order to control the new ACL engine behavior
- **BREAKING**: the *Burp1* and *Burp2* configuration sections have been merged into one single *Burp* section
- **BREAKING**: the *running* backups are now displayed in ``green`` instead of ``blue``
- **BREAKING**: the docker postgresql image was upgraded from 9.6 to 10.1, you'll have to manually upgrade/migrate your data `following this documentation <https://github.com/tianon/docker-postgres-upgrade>`_
- **BREAKING**: the ``docker-compose.yml`` file now uses the ``version: '2'`` format
- **BREAKING**: the old config file format with colons (:) as separator is no
- Add: new plugins system to allow users to write their own modules
- Add: `Italian translation <https://git.ziirish.me/ziirish/burp-ui/merge_requests/74>`_ thanks to Enrico
- Add: new `client configuration templates <https://git.ziirish.me/ziirish/burp-ui/issues/155>`_
- Add: `backups deletion <https://git.ziirish.me/ziirish/burp-ui/issues/203>`_
- Add: `show last client status in client view <https://git.ziirish.me/ziirish/burp-ui/issues/212>`_
- Add: `record login failure attempt <https://git.ziirish.me/ziirish/burp-ui/issues/214>`_
- Add: `support new burp counters <https://git.ziirish.me/ziirish/burp-ui/issues/219>`_
- Add: `support new burp pair options <https://git.ziirish.me/ziirish/burp-ui/issues/220>`_
- Add: `support new reset list (:=) syntax <https://git.ziirish.me/ziirish/burp-ui/issues/223>`_
- Add: `new websocket server <https://git.ziirish.me/ziirish/burp-ui/issues/224>`_
- Add: `new Administration panel <https://git.ziirish.me/ziirish/burp-ui/issues/222>`_
- Improvement: `better ACL engine <https://git.ziirish.me/ziirish/burp-ui/issues/221>`_
- Fix: issue `#213 <https://git.ziirish.me/ziirish/burp-ui/issues/213>`_
- Fix: issue `#225 <https://git.ziirish.me/ziirish/burp-ui/issues/225>`_
- Fix: issue `#226 <https://git.ziirish.me/ziirish/burp-ui/issues/226>`_
- Fix: issue `#227 <https://git.ziirish.me/ziirish/burp-ui/issues/227>`_
- Fix: issue `#234 <https://git.ziirish.me/ziirish/burp-ui/issues/234>`_
- Fix: issue `#235 <https://git.ziirish.me/ziirish/burp-ui/issues/235>`_
- Fix: issue `#236 <https://git.ziirish.me/ziirish/burp-ui/issues/236>`_
- Fix: issue `#242 <https://git.ziirish.me/ziirish/burp-ui/issues/242>`_
- Fix: issue `#245 <https://git.ziirish.me/ziirish/burp-ui/issues/245>`_
- Fix: issue `#246 <https://git.ziirish.me/ziirish/burp-ui/issues/246>`_
- Fix: issue `#247 <https://git.ziirish.me/ziirish/burp-ui/issues/247>`_
- Fix: issue `#248 <https://git.ziirish.me/ziirish/burp-ui/issues/248>`_
- Fix: issue `#251 <https://git.ziirish.me/ziirish/burp-ui/issues/251>`_
- Fix: issue `#257 <https://git.ziirish.me/ziirish/burp-ui/issues/257>`_
- Fix: issue `#262 <https://git.ziirish.me/ziirish/burp-ui/issues/262>`_
- Fix: issue `#263 <https://git.ziirish.me/ziirish/burp-ui/issues/263>`_
- Fix: issue `#264 <https://git.ziirish.me/ziirish/burp-ui/issues/264>`_
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/0.5.0...0.6.0>`__

0.5.1 (05/26/2017)
------------------

- Fix: handle non ascii chars in the browser view
- Fix: issue `#215 <https://git.ziirish.me/ziirish/burp-ui/issues/215>`_
- Fix: issue `#218 <https://git.ziirish.me/ziirish/burp-ui/issues/218>`_

0.5.0 (05/09/2017)
------------------

- **BREAKING**: the *standalone* option has been renamed to *single* for less confusion
- **BREAKING**: the ``bui-agent`` has now its own independent package to reduce dependencies
- Add: `Spanish translation <https://git.ziirish.me/ziirish/burp-ui/merge_requests/66>`_ thanks to Pablo
- Add: `reverse_proxy option <https://git.ziirish.me/ziirish/burp-ui/merge_requests/65>`_ while running through gunicorn
- Add: `OS detection for burp 2 <https://git.ziirish.me/ziirish/burp-ui/issues/200>`_
- Add: `customizable reports <https://git.ziirish.me/ziirish/burp-ui/issues/187>`_
- Add: persistent storage for user preferences if SQL storage enabled
- Add: rate-limiting of the API
- Add: new ``diag`` and ``sysinfo`` commands to help you diagnose issues
- Improvement: the SQL storage will detect out-of-sync schemas and disable itself if needed (with a log message)
- Improvement: speedup the calendar view
- Improvement: more complete user panel (`#185 <https://git.ziirish.me/ziirish/burp-ui/issues/185>`_, `#184 <https://git.ziirish.me/ziirish/burp-ui/issues/184>`_, `#182 <https://git.ziirish.me/ziirish/burp-ui/issues/182>`_, `#132 <https://git.ziirish.me/ziirish/burp-ui/issues/132>`_)
- Fix: issue `#186 <https://git.ziirish.me/ziirish/burp-ui/issues/186>`_
- Fix: issue `#192 <https://git.ziirish.me/ziirish/burp-ui/issues/192>`_
- Fix: issue `#194 <https://git.ziirish.me/ziirish/burp-ui/issues/194>`_
- Fix: issue `#196 <https://git.ziirish.me/ziirish/burp-ui/issues/196>`_
- Fix: issue `#198 <https://git.ziirish.me/ziirish/burp-ui/issues/198>`_
- Fix: issue `#210 <https://git.ziirish.me/ziirish/burp-ui/issues/210>`_
- Various bugfix
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.4.0...v0.5.0>`__

0.4.4 (01/02/2017)
------------------

- Fix: issue `#193 <https://git.ziirish.me/ziirish/burp-ui/issues/193>`_

0.4.3 (12/28/2016)
------------------

- Fix: issue `#186 <https://git.ziirish.me/ziirish/burp-ui/issues/186>`_
- Fix: issue `#188 <https://git.ziirish.me/ziirish/burp-ui/issues/188>`_
- Fix: issue `#190 <https://git.ziirish.me/ziirish/burp-ui/issues/190>`_
- Fix: missing configuration in docker image
- Fix: help troubleshooting some errors
- Fix: missing vss_strip binary
- Fix: encoding error that made unable to browse backups with burp1 backend

0.4.2 (12/16/2016)
------------------

- Fix: bui-agent was broken
- Fix: handle i18n exceptions
- Fix: enable db migration only when needed
- Fix: wrong escape in translation

0.4.1 (12/15/2016)
------------------

- **BREAKING**: Use the new Flask's embedded server by default means no more SSL (HTTPS) support without a dedicated application server
- Fix: issue `#156 <https://git.ziirish.me/ziirish/burp-ui/issues/156>`_
- Fix: issue `#157 <https://git.ziirish.me/ziirish/burp-ui/issues/157>`_
- Fix: issue `#165 <https://git.ziirish.me/ziirish/burp-ui/issues/165>`_
- Fix: issue `#176 <https://git.ziirish.me/ziirish/burp-ui/issues/176>`_
- Fix: issue `#181 <https://git.ziirish.me/ziirish/burp-ui/issues/181>`_
- Fix: issue `#182 <https://git.ziirish.me/ziirish/burp-ui/issues/182>`_
- Various bugfix
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.4.0...v0.4.1>`__

0.4.0 (11/23/2016)
------------------

- **BREAKING**: The database schema evolved. In order to apply these modifications, you **MUST** run the ``bui-manage db upgrade`` command after upgrading
- **BREAKING**: Plain text passwords are deprecated since v0.3.0 and are now disabled by default
- **BREAKING**: The default *version* setting has been set to ``2`` instead of ``1``
- Add: new `bui-manage setup_burp <https://git.ziirish.me/ziirish/burp-ui/merge_requests/40#note_1767>`_ command
- Add: new `docker image <https://git.ziirish.me/ziirish/burp-ui/merge_requests/40#note_1763>`_
- Add: manage `user sessions <https://git.ziirish.me/ziirish/burp-ui/merge_requests/6>`_
- Add: `French translation <https://git.ziirish.me/ziirish/burp-ui/merge_requests/4>`_
- Fix: issue `#151 <https://git.ziirish.me/ziirish/burp-ui/issues/151>`_
- Fix: issue `#154 <https://git.ziirish.me/ziirish/burp-ui/issues/154>`_
- Fix: issue `#158 <https://git.ziirish.me/ziirish/burp-ui/issues/158>`_
- Fix: issue `#163 <https://git.ziirish.me/ziirish/burp-ui/issues/163>`_
- Fix: issue `#164 <https://git.ziirish.me/ziirish/burp-ui/issues/164>`_
- Fix: issue `#166 <https://git.ziirish.me/ziirish/burp-ui/issues/166>`_
- Fix: issue `#169 <https://git.ziirish.me/ziirish/burp-ui/issues/169>`_
- Fix: issue `#171 <https://git.ziirish.me/ziirish/burp-ui/issues/171>`_
- Fix: issue `#172 <https://git.ziirish.me/ziirish/burp-ui/issues/172>`_
- Fix: issue `#173 <https://git.ziirish.me/ziirish/burp-ui/issues/173>`_
- Fix: issue `#174 <https://git.ziirish.me/ziirish/burp-ui/issues/174>`_
- Various bugfix
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.3.0...v0.4.0>`__

0.3.0 (08/15/2016)
------------------

- **BREAKING**: New configuration file format to allow further improvements (The conversion is automatic, but LDAP settings might need some attention)
- **BREAKING**: Passwords are now *salted* for the *BASIC* authentication backend (The conversion is automatic too)
- **BREAKING**: If you plan to use the SQL storage along with gunicorn, you **MUST** add the *--preload* parameter (see the *gunicorn.d/burp-ui* file)
- Add: `Celery <http://www.celeryproject.org/>`_ support for asynchronous tasks
- Add: `SQLAlchemy <http://www.sqlalchemy.org/>`_ support for persistent storage
- Add: `RESTful restore <https://git.ziirish.me/ziirish/burp-ui/issues/111>`_
- Add: `autoreload config <https://git.ziirish.me/ziirish/burp-ui/issues/142>`_
- Add: `remember some user settings <https://git.ziirish.me/ziirish/burp-ui/issues/133>`_
- Add: `client certificate revocation <https://git.ziirish.me/ziirish/burp-ui/issues/131>`_
- Add: new `local authentication backend <https://git.ziirish.me/ziirish/burp-ui/issues/130>`_
- Add: new `filters on history API call <https://git.ziirish.me/ziirish/burp-ui/issues/140>`_
- Add: implement backend `keepalive <https://git.ziirish.me/ziirish/burp-ui/issues/98>`_
- Add: allow to *disable* `server-initiated restoration <https://git.ziirish.me/ziirish/burp-ui/issues/136>`_
- Fix: disable Basic-Auth login from UI to prevent some bugs with sessions
- Fix: issue `#134 <https://git.ziirish.me/ziirish/burp-ui/issues/134>`_
- Fix: issue `#135 <https://git.ziirish.me/ziirish/burp-ui/issues/135>`_
- Fix: issue `#137 <https://git.ziirish.me/ziirish/burp-ui/issues/137>`_
- Fix: issue `#138 <https://git.ziirish.me/ziirish/burp-ui/issues/138>`_
- Fix: issue `#145 <https://git.ziirish.me/ziirish/burp-ui/issues/145>`_
- Fix: issue `#148 <https://git.ziirish.me/ziirish/burp-ui/issues/148>`_
- Improvement: new asynchronous `backup-running API call <https://git.ziirish.me/ziirish/burp-ui/issues/139>`_
- Security: restrict files that can be sent by the agent
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.2.1...v0.3.0>`__

0.2.1 (05/17/2016)
------------------

- Add: allow to `edit a server-initiated restoration <https://git.ziirish.me/ziirish/burp-ui/issues/125>`_
- Add: allow to `cancel a server-initiated restoration <https://git.ziirish.me/ziirish/burp-ui/issues/112>`_
- Add: support for `Burp labels <https://git.ziirish.me/ziirish/burp-ui/issues/116>`_
- Add: `server-initiated backups <https://git.ziirish.me/ziirish/burp-ui/issues/119>`_
- Add: support `sub-root path <https://git.ziirish.me/ziirish/burp-ui/issues/128>`_
- Add: new Burp 2 settings
- Improvement: `better logging system <https://git.ziirish.me/ziirish/burp-ui/issues/118>`_
- Improvement: `new security options <https://git.ziirish.me/ziirish/burp-ui/issues/86>`_
- Fix: issue `#109 <https://git.ziirish.me/ziirish/burp-ui/issues/109>`_
- Fix: issue `#113 <https://git.ziirish.me/ziirish/burp-ui/issues/113>`_
- Fix: issue `#114 <https://git.ziirish.me/ziirish/burp-ui/issues/114>`_
- Fix: issue `#117 <https://git.ziirish.me/ziirish/burp-ui/issues/117>`_
- Fix: issue `#123 <https://git.ziirish.me/ziirish/burp-ui/issues/123>`_
- Doc
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.1.0...v0.2.0>`__

0.1.3 (02/20/2016)
------------------

- Fix: issue `#107 <https://git.ziirish.me/ziirish/burp-ui/issues/107>`_
- Fix: issue `#108 <https://git.ziirish.me/ziirish/burp-ui/issues/108>`_

0.1.2 (02/18/2016)
------------------

- Fix: duration computation
- Fix: issue `#104 <https://git.ziirish.me/ziirish/burp-ui/issues/104>`_
- Fix: issue `#105 <https://git.ziirish.me/ziirish/burp-ui/issues/105>`_
- Fix: issue `#106 <https://git.ziirish.me/ziirish/burp-ui/issues/106>`_

0.1.1 (02/17/2016)
------------------

- Fix: burp2 backend issue
- Fix: Debian wheezy compatibility
- Fix: sample configuration files location
- Better calendar readability

0.1.0 (02/15/2016)
------------------

- Add: `python 3 support <https://git.ziirish.me/ziirish/burp-ui/issues/75>`_
- Add: new fields in `backup reports <https://git.ziirish.me/ziirish/burp-ui/issues/48>`_
- Add: `server-side initiated restoration <https://git.ziirish.me/ziirish/burp-ui/issues/12>`_
- Add: percent done in `overview <https://git.ziirish.me/ziirish/burp-ui/issues/55>`_
- Add: ability to `chain multiple authentication backends <https://git.ziirish.me/ziirish/burp-ui/issues/79>`_
- Add: display versions `within the interface <https://git.ziirish.me/ziirish/burp-ui/issues/89>`_
- Add: support for `zip64 <https://git.ziirish.me/ziirish/burp-ui/issues/97>`_
- Add: new `report <https://git.ziirish.me/ziirish/burp-ui/issues/15>`_
- Add: new `calendar view <https://git.ziirish.me/ziirish/burp-ui/issues/61>`_
- Add: "restart" option to debian init script thanks to @Larsen
- Add: Basic HTTP Authentication (mostly for the API)
- Add: self-documented API
- Fix: issue `#81 <https://git.ziirish.me/ziirish/burp-ui/issues/81>`_
- Fix: issue `#87 <https://git.ziirish.me/ziirish/burp-ui/issues/87>`_
- Fix: issue `#88 <https://git.ziirish.me/ziirish/burp-ui/issues/88>`_
- Fix: issue `#92 <https://git.ziirish.me/ziirish/burp-ui/issues/92>`_
- Fix: issue `#95 <https://git.ziirish.me/ziirish/burp-ui/issues/95>`_
- Fix: issue `#99 <https://git.ziirish.me/ziirish/burp-ui/issues/99>`_
- Fix: issue `#100 <https://git.ziirish.me/ziirish/burp-ui/issues/100>`_
- Fix: issue `#101 <https://git.ziirish.me/ziirish/burp-ui/issues/101>`_
- `demo <https://demo.burp-ui.org/>`_
- API refactoring
- Security fixes
- Bugfixes

0.0.7.3 (09/26/2015)
--------------------

- Fix: issue `#77 <https://git.ziirish.me/ziirish/burp-ui/issues/77>`_
- Doc

0.0.7.2 (09/01/2015)
--------------------

- Fix: issue `#73 <https://git.ziirish.me/ziirish/burp-ui/issues/72>`_
- Fix: issue `#74 <https://git.ziirish.me/ziirish/burp-ui/issues/74>`_
- Doc

0.0.7.1 (08/22/2015)
--------------------

- Add: `Burp-2 backend <https://git.ziirish.me/ziirish/burp-ui/issues/52>`_
- Add: `sortable tables <https://git.ziirish.me/ziirish/burp-ui/issues/51>`_
- Add: `ACL support <https://git.ziirish.me/ziirish/burp-ui/issues/47>`_
- Add: `support client-side encrypted backups while performing an online restoration <https://git.ziirish.me/ziirish/burp-ui/issues/44>`_
- Add: `multiple archive format <https://git.ziirish.me/ziirish/burp-ui/issues/31>`_
- Add: `better Active Directory support <https://git.ziirish.me/ziirish/burp-ui/issues/64>`__
- Improvement: `better config file parser <https://git.ziirish.me/ziirish/burp-ui/issues/50>`_
- Improvement: `better logging with Gunicorn <https://git.ziirish.me/ziirish/burp-ui/issues/65>`_
- Improvement: `full support of server configuration file + clientconfdir <https://git.ziirish.me/ziirish/burp-ui/issues/13>`_
- Fix: issue `#35 <https://git.ziirish.me/ziirish/burp-ui/issues/35>`_
- Fix: issue `#37 <https://git.ziirish.me/ziirish/burp-ui/issues/37>`_
- Fix: issue `#41 <https://git.ziirish.me/ziirish/burp-ui/issues/41>`_
- Fix: issue `#42 <https://git.ziirish.me/ziirish/burp-ui/issues/42>`_
- Fix: issue `#46 <https://git.ziirish.me/ziirish/burp-ui/issues/46>`_
- Fix: issue `#49 <https://git.ziirish.me/ziirish/burp-ui/issues/49>`_
- Fix: issue `#53 <https://git.ziirish.me/ziirish/burp-ui/issues/53>`_
- Fix: issue `#54 <https://git.ziirish.me/ziirish/burp-ui/issues/54>`_
- Fix: issue `#59 <https://git.ziirish.me/ziirish/burp-ui/issues/59>`_
- Fix: issue `#62 <https://git.ziirish.me/ziirish/burp-ui/issues/62>`_
- Fix: issue `#68 <https://git.ziirish.me/ziirish/burp-ui/issues/68>`_
- Fix: issue `#69 <https://git.ziirish.me/ziirish/burp-ui/issues/69>`_
- Fix: issue `#70 <https://git.ziirish.me/ziirish/burp-ui/issues/70>`_
- Fix: issue `#71 <https://git.ziirish.me/ziirish/burp-ui/issues/71>`_
- Fix: issue `#72 <https://git.ziirish.me/ziirish/burp-ui/issues/72>`_
- doc on `readthedocs <http://burp-ui.readthedocs.io/en/latest/>`_
- Two merge requests from Wade Fitzpatrick (`!1 <https://git.ziirish.me/ziirish/burp-ui/merge_requests/1>`_ and `!2 <https://git.ziirish.me/ziirish/burp-ui/merge_requests/2>`_)
- API refactoring
- Security fixes
- Bufixes
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.6...v0.0.7.1>`__

0.0.6 (12/15/2014)
------------------

- Add: `gunicorn support <https://git.ziirish.me/ziirish/burp-ui/commit/836f522f51ba0706ca94b379d93b20c75e71ecb1>`_
- Add: `init script for CentOS <https://git.ziirish.me/ziirish/burp-ui/issues/27>`_
- Add: `init script for Debian <https://git.ziirish.me/ziirish/burp-ui/issues/29>`_
- Add: `autofocus login field on login page <https://git.ziirish.me/ziirish/burp-ui/commit/a559c3c2191991f1065ff15df4cd94757133e67d>`_
- Add: `burp-server configuration panel <https://git.ziirish.me/ziirish/burp-ui/issues/13>`_
- Fix: issue `#25 <https://git.ziirish.me/ziirish/burp-ui/issues/25>`_
- Fix: issue `#26 <https://git.ziirish.me/ziirish/burp-ui/issues/26>`_
- Fix: issue `#30 <https://git.ziirish.me/ziirish/burp-ui/issues/30>`_
- Fix: issue `#32 <https://git.ziirish.me/ziirish/burp-ui/issues/32>`_
- Fix: issue `#33 <https://git.ziirish.me/ziirish/burp-ui/issues/33>`_
- Fix: issue `#34 <https://git.ziirish.me/ziirish/burp-ui/issues/34>`_
- Fix: issue `#35 <https://git.ziirish.me/ziirish/burp-ui/issues/35>`_
- Fix: issue `#39 <https://git.ziirish.me/ziirish/burp-ui/issues/39>`_
- Code cleanup
- Improve unit tests
- Bugfixes
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.5...v0.0.6>`__

0.0.5 (09/22/2014)
------------------

- Add: multi-server support
- Fix bugs
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.4...v0.0.5>`__

0.0.4 (09/07/2014)
------------------

- Add: ability to download files directly from the web interface
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.3...v0.0.4>`__

0.0.3 (09/02/2014)
------------------

- Add: authentication
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.2...v0.0.3>`__

0.0.2 (08/25/2014)
------------------

- Fix bugs
- `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.1...v0.0.2>`__

0.0.1 (08/25/2014)
------------------

- Initial release
