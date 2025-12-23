1. - # 每天的请求量是多少

     大概几万或者十几万的一个量级。 

     

     如果按照每秒的并发？ qps是在是多少左右？

     

     

     

     

     

     

     # 数据量多少 选择哪种存储方式

     数据量可能在TB 级别。

     

     那么 以下的数据库选择哪个比较合适

     1. mysql?  高并发性能不好。日志信息写入频繁，mysql需要动态维护B+索引结构，插入性能差。
     2. es ? 全文搜索 错误日志检索 运维难度高 内存占用高，检索速度快 适合做系统运行日志监控平台，不适合做埋点日志分析平台 ❌	
     3.   clickhouse?  高压缩率  节省空间。支持TB 级的存储   OLAP（联机分析处理）数据库 适合埋点数据的聚合查询，比如算平均值，求和，去重等。支持sql。 ✅

     

     ```python
     # 测试数据：1亿条Nginx日志（原始大小500GB）
     ClickHouse:
       - 压缩后: 50GB (10:1压缩比)
       - 查询内存: 2-4GB
     
     Elasticsearch:
       - 压缩后: 250GB (2:1压缩比)
       - JVM堆内存: 32GB+
       - 磁盘I/O: 高
     ```

     

     

     

     # 埋点日志格式

     根据需求 设计请求数据的格式。

     大概有以下这么几种设计风格

     

     

     https://blog.csdn.net/goTsHgo/article/details/143307009

     

     

     

     

     

     

     

     # 是离线处理日志还是实时处理日志

     意思是 运营方需要实时查看埋点数据分析  还是 分批收集埋点数据之后在某一个时间点统一分析。

     

     

     

     

     # 日志收集组件

     在我们的需求当中需要采集nginx 的请求日志，所以就需要有对应的日志采集组件。以下是主流的采集组件。

     

     

     1. flume
     2. logstash
     3. filebeat

     这篇文章是关于他们之间对比的介绍

     https://cloud.tencent.com/developer/article/1651643

     

     总结来说 从占用资源角度来说 flume > logstash > filebeat

     logstash 和 filebeat是同一个生态里面的组件。  logstash 侧重于 数据过滤 filebeat 侧重于数据采集。

     所以一般 将 filebeat和 logstash 搭配使用。

     ```python
     为什么这么选？
     Filebeat擅长收集：文件监控、断点续传、负载均衡
     
     Logstash擅长处理：强大的grok、丰富的插件、易调试
     
     分工明确：各司其职，架构清晰
     
     易于扩展：未来需要更复杂处理时，直接在Logstash中添加
     
     配置要点
     Filebeat：只做收集，关闭复杂处理
     
     Logstash：承担所有解析和转换逻辑
     
     ClickHouse：接收结构化数据，专注于存储和查询
     ```

     

     下面这篇文章是关于 filebeat 和 logstash 搭配使用的案例  这篇文章在filebeat和logstash 之间加了一个 kafka 。有这么几个作用，

     1. filebeat 的采集速度是优于logstash 的。 可以加入 kafka作为流量的缓冲。
     2. 解耦，将filebeat和logstash解耦，filebeat只要关心把数据丢给kafka就行。不需要关心谁在处理数据。
     3. 内容分发，同一份日志数据可以由kafka分发给多个消费者消费。

     

     kafka是一个可选项，由于我们是从nginx本地日志文件读取。这个读取的速度是可以控制的。所以kafka并不是一个必选的。

     https://help.aliyun.com/zh/es/use-cases/use-filebeat-kafka-logstash-and-elasticsearch-to-build-a-log-analysis-system

     

     

     ![img](https://cdn.nlark.com/yuque/0/2025/png/28467887/1766394135177-8d64d2a8-c54b-4b36-94e8-d23d8b58169b.png)

     

     

     

     这篇文章是 介绍 三种采集nginx 日志的方式

     https://cloud.tencent.com/developer/article/1895982

     

     

     

     # 可视化分析界面

     如果需要可视化的分析界面 以下有开源免费的选择

      QuickBI / Metabase  

     

     

     # 方案一 nginx +logrotate+ filebeat + logstash +clickhouse

     

     这个方案设计 足够支撑每天 几万到十几万的请求日志了。  

     

     ## 架构设计

     ```python
     Nginx (生产日志) -> Filebeat (采集) -> Logstash (清洗/转换) -> ClickHouse (存储)
     ```

     **nginx:** 通过http请求发送到nginx , nginx 将请求的数据写入本地日志文件。

     **Filebeat:** 负责数据采集，可并行读取多个文件。

     **logrotate：**linux系统上的一个日志分割组件，由于nginx的日志写入是追加模式，如果不进行分割，单个access.log 文件会堆积十几G的数据。

     **logstash：**logstash 负责清洗过滤原始日志数据

     **ClickHouse  ：**结构化存储logstash 清洗之后的数据。 TB 级数据存储成本很低，且查询速度极快。

     

     

     ## 示例执行步骤

     

     ### 一、nginx 请求格式定义

     这个可按需设计，例如最常用的json格式

     ```python
     http {
         # 定义一个 JSON 格式的日志结构
         log_format json_analytics escape=json '{'
             '"time_local": "$time_local",'
             '"remote_addr": "$remote_addr",'
             '"request_uri": "$request_uri",'
             '"request_method": "$request_method",'
             '"status": "$status",'
             '"body_bytes_sent": "$body_bytes_sent",'
             '"http_referer": "$http_referer",'
             '"http_user_agent": "$http_user_agent",'
             '"x_forwarded_for": "$http_x_forwarded_for"'
         '}';
     
         server {
             # 埋点接口使用该日志格式
             location /track {
                 # 业务逻辑...
                 access_log /var/log/nginx/track_access.log json_analytics;
             }
         }
     }
     ```

     

       

     ### 二、clickhouse建表

      使用 `MergeTree` 引擎，按天分区。  

     ```python
     CREATE TABLE analytics_log
     (
         event_time DateTime,
         event_date Date DEFAULT toDate(event_time),
         remote_ip String,
         city String,           -- 由 Logstash 解析后填入
         request_uri String,
         request_params String, -- 原始参数
         event_type String,     -- 从参数中提取
         user_id String,        -- 从参数中提取
         device_os String,      -- 由 Logstash 解析 UserAgent 填入
         browser String,
         status UInt16
     )
     ENGINE = MergeTree()
     PARTITION BY event_date
     ORDER BY (event_time, event_type) -- 排序键，加速查询
     TTL event_date + INTERVAL 1 YEAR -- 数据保留1年，自动删除
     SETTINGS index_granularity = 8192;
     ```

     

     ### 三、 采集端 (Filebeat 配置)  

      控制并发，防止抢占 Nginx 资源。  

     ```python
     filebeat.inputs:
     - type: log
       enabled: true
       paths:
         - /var/log/nginx/track_access.log
       json.keys_under_root: true  # 直接解析 Nginx 的 JSON
       json.overwrite_keys: true
       
       # 【重要】限速配置，防止没有 Kafka 时打垮下游
       harvester_limit: 2          # 限制同时读取的文件数
     
     output.logstash:
       hosts: ["<Logstash_IP>:5044"]
       # 减小批量发送大小，平滑流量
       bulk_max_size: 200
     ```

     

     

     

     ###  四、加工厂 (Logstash 配置)  

      提取 URL 参数，解析 IP 和 UserAgent，批量写入 ClickHouse。  

     你需要安装 ClickHouse 插件：`bin/logstash-plugin install logstash-output-clickhouse`

     

     ```python
     input {
       beats {
         port => 5044
       }
     }
     
     filter {
       # 1. 解析时间格式 (Nginx 的时间格式需要转换)
       date {
         match => ["time_local", "dd/MMM/yyyy:HH:mm:ss Z"]
         target => "event_time"
       }
     
       # 2. 解析 UserAgent (获取 操作系统、浏览器)
       useragent {
         source => "http_user_agent"
         target => "ua_parsed"
       }
     
       # 3. 解析 IP 地址 (获取 城市、国家)
       geoip {
         source => "remote_addr"
       }
       
       # 4. 提取 URL 中的参数 (例如 ?event=login&uid=123)
       # 这里假设你只需要把整个 URI 存下来，或者你可以用 ruby/kv 插件拆分
     }
     
     output {
       clickhouse {
         http_hosts => ["http://<ClickHouse_IP>:8123"]
         table => "analytics_log"
         # 字段映射：左边是 ClickHouse 字段，右边是 Logstash 字段
         mutations => {
           "remote_ip" => "remote_addr"
           "city" => "[geoip][city_name]"
           "device_os" => "[ua_parsed][os]"
           "browser" => "[ua_parsed][name]"
           "request_uri" => "request_uri"
           "status" => "status"
         }
         # 【关键】批量写入配置，保护数据库
         flush_size => 5000     # 攒够 5000 条写一次
         idle_flush_time => 10  # 或攒够 10 秒写一次
       }
     }
     ```

     

     

     

     

     # 方案二 云服务器方案  ❌ 采用自研方案

     

     之前的埋点使用bigquery 进行存储吗？

     - **数据收集**：使用云服务商提供的埋点SDK（如AWS Amplify、Google Analytics的SDK）。
     - **数据传输**：SDK直接发送到云服务商的网关。
     - **数据存储**：存储在云存储（如AWS S3、Google Cloud Storage）和云数据仓库（如AWS Redshift、Google BigQuery）中。
     - **数据分析**：使用云上的BI工具（如AWS QuickSight、Google Data Studio）或直接使用SQL查询数据仓库。

     #### 

     # 方案三  使用第三方分析平台 ❌采用自研方案

     - **数据收集**：使用第三方分析平台（如Mixpanel、神策数据、GrowingIO）提供的SDK。
     - **数据传输**：SDK直接发送到第三方平台。
     - **数据存储和分析**：由第三方平台负责，用户通过其提供的界面进行数据分析。