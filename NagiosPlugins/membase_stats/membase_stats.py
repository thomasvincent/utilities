#!/usr/bin/env python
# ./membase_stats.py

import subprocess
import getopt
import sys
import urllib
import urllib2
import base64
import json

class MembaseStats:
#mapping a list of resource name we are keeping the state
    resource_name_mapping = {
        "curr_items": {"description": "Current active items", "unit": "", "type": "current", "name": "current_active_items"},
        "curr_items_tot": {"description": "Current total items", "unit": "", "type": "current", "name": "current_total_items"},
        "ep_num_active_non_resident": {"description": "Current non-resident item", "unit": "", "type": "current", "name": "num_active_items_not_in_RAM"},
        "get_hits": {"description": "Number of fetches", "unit": "", "type": "cumulative", "name": "num_successful_get"},
        "ep_bg_fetched": {"description": "Number of items fetched from the disk", "unit": "", "type": "cumulative", "name": "num_items_get_from_disk" },
        "ep_num_non_resident": {"description": "Number of items stored only on disk, not cached in RAM", "unit": "", "type": "current", "name": "num_total_items_not_in_RAM"},
        "ep_total_enqueued": {"description": "Total number of items queued for storage" , "unit": "", "type": "cumulative", "name": "total_items_enqueued_for_storage"},
        "ep_total_new_items": {"description": "Total number of persisted new items", "unit": "", "type": "cumulative", "name": "num_persisted_new_items"},
        "get_misses": {"description": "Number of unsuccessful fetches", "unit": "", "type": "cumulative", "name": "num_unsuccessful_get"},
        "mem_used": {"description": "Current memory usage", "unit": "B", "type": "current", "name": "memory_usage"},
        "ep_total_cache_size": {"description": "Cache size", "unit": "B", "type": "current", "name": "total_cache_size"},
        "bytes_written": {"description": "Number of bytes written", "unit": "B", "type": "cumulative", "name": "bytes_written"},
        "ep_queue_size": {"description": "Number of items in the disk written queue", "unit": "", "type": "current", "name": "disk_write_queue_size"},
        "ep_io_num_write": {"description": "Number of io write operations", "unit": "", "type": "cumulative", "name": "num_io_write_operations"},
        "ep_io_num_read": {"description": "Number of io read operations", "unit": "", "type": "cumulative", "name": "num_io_read_operations"},
        "ep_total_persisted": {"description": "Total number of persisted items", "unit": "", "type": "cumulative", "name": "num_items_persisted"},
        "ep_total_del_items": {"description": "Total number of persisted deletions", "unit": "", "type": "cumulative", "name": "num_items_deleted"},
        "ep_item_commit_failed": {"description": "Number of times a transaction failed to commit due to storage errors", "unit": "", "type": "cumulative", "name": "num_failed_transactions"},
        "ep_expired": {"description": "Number of times an item was expired", "unit": "", "type": "cumulative", "name": "expired_items"},
        }

    #data_file_name = "/usr/share/appfirst/plugins/membase_stats_data"
    data_file_name = "./membase_stats_data"
    prev_stats = {}
    d_stats = {}
    list = False
    # get the previous value from the data we kept
    def before_work(self):
        try:
            file = open(self.data_file_name, 'r')
            for line in file.readlines():# read all the previous value line by line
                items = line.split()
                if len(items) > 1:
                    resource_name = items[0]
                    resource_value = items[1]
                    try:
                        self.prev_stats[resource_name] = int(resource_value)
                    except Exception,e:
                        pass
            file.close()
        except Exception,e:
            pass

    def after_work(self):
        try:
            file = open(self.data_file_name, 'w')
            file_content = ""
            for key in self.prev_stats:
                file_content += ("%s %d\n" % (key, self.prev_stats[key]))
            file.write(file_content)
            file.close()
        except:
            pass

    def usage(self):
        print "usage:\n\tmembase_stats.py [-l|--list|-h|--help|--url=URL|--username=USER|--password=PASS]\n\tmembase_stats.py metric|all\n\t\tWhere metric is one of the metrics shown with a -l|--list"

    def get_status(self, src_url, remote_user, remote_pass):
        request = urllib2.Request(src_url)
        base64string = base64.encodestring('%s:%s' % (remote_user, remote_pass)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)
        content = result.read()
        parsed = json.loads(content)
        parsed = parsed["op"]["samples"]
        str_stats = ""
        for each in parsed.keys():
            str_stats += ("%s:  %s\n") % (each,parsed[each][-1])
        #print str_stats
        #sys.exit(1)
        '''str_stats = subprocess.Popen("/opt/membase/bin/ep_engine/management/stats 127.0.0.1:11210 all",
            shell = True, stdout=subprocess.PIPE).communicate()[0]
        stats = str_stats.split('\n')'''
        stats = str_stats.split('\n')
        # = content.split('\n','')
        #print stats
        for i in range(len(stats) - 1):
            j = stats[i].index(':')
            k = stats[i].rindex(' ')

            try:
                self.d_stats[stats[i][1:j]] = int(stats[i][k+1:])
            except ValueError:
                self.d_stats[stats[i][1:j]] = stats[i][k+1:]

    def main(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "lh", ["list", "help", "url=", "username=", "password="])
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)

        self.prev_stats = {}
        self.d_stats = {}
        self.before_work()
        ####################
        self.url = None
        self.username = None
        self.password = None
        ####################
        for o, a in opts:
            if (o in ("--url")):
                self.url = a
            if (o in ("--username")):
                self.username = a
            if (o in ("--password")):
                self.password = a
            if (o in ("-l")) or (o in ("--list")):
                self.list = True
            if (o in ("-h")) or o in ("--help"):
                self.usage()
                sys.exit(0)

        self.get_status(src_url=self.url, remote_user=self.username, remote_pass=self.password)

        if self.list is True:
            for k in self.self.d_stats.iterkeys():
                print k
            sys.exit(0)
            #
        # Nagios developer docs define perfomance data format as:
        #    'label'=value[UOM];[warn];[crit];[min];[max]
        # Example from check_http:
        #    HTTP OK: HTTP/1.1 200 OK - 8683 bytes in 1.196 second response time |time=1.196437s;5.000000;10.000000;0.000000 size=8683B;;;0 ec="0"
        #
        perf_data = "Membase_Stats:OK | "

        if not args:
            args.append("all")

        if "all" in args:
            keys = self.d_stats.iterkeys()
        else:
            keys = args

        for key in keys:
            perf_data += self.process_data(key)
        perf_data += self.get_resident_ratio()
        perf_data += self.get_cache_miss_ratio()
        perf_data += self.get_replica_resident_ratio()
        print perf_data
        self.after_work()

    def process_data(self, key):
        ret = " "
        if self.resource_name_mapping.has_key(key):
            type = "current"
            name = key
            if self.resource_name_mapping[key].has_key('name'):
                name = self.resource_name_mapping[key]['name']
            if self.resource_name_mapping[key].has_key('type'):
                type = self.resource_name_mapping[key]['type']
            if type == "cumulative":
                tmp = self.d_stats[key]
                if self.prev_stats.has_key(key):
                    self.d_stats[key] = self.d_stats[key] - self.prev_stats[key]
                    if self.d_stats[key] < 0: #somehow membase is reseted
                        tmp = 0
                    else:
                        ret = "%s=%s%s " % (name, self.d_stats[key], self.resource_name_mapping[key]['unit'])
                self.prev_stats[key] = tmp # update the value we are keeping track of
            else:
                ret = "%s=%s%s " % (name, self.d_stats[key], self.resource_name_mapping[key]['unit'])
        else:
            ret = "%s=%s " % (key,self.d_stats[key])
        return ret

    def get_resident_ratio(self):
        resident_item_ratio = 100
        if self.d_stats.has_key('ep_num_active_non_resident') and self.d_stats.has_key('curr_items')\
        and self.d_stats['curr_items'] > 0:
            resident_item_ratio = 100 - float(self.d_stats['ep_num_active_non_resident']) / float(self.d_stats['curr_items']) * 100
        if resident_item_ratio < 0:
            resident_item_ratio = 0
        return "%s=%s%s " % ('resident_item_ratio', resident_item_ratio, '%')

    def get_cache_miss_ratio(self):
        cache_miss_ratio = 0
        if self.d_stats.has_key('get_hits') and self.d_stats.has_key('ep_bg_fetched') and self.d_stats['get_hits'] > 0:
            cache_miss_ratio = float(self.d_stats['ep_bg_fetched']) / float(self.d_stats['get_hits']) * 100
        return "%s=%s%s " % ('cache_miss_ratio', cache_miss_ratio, '%')

    def get_replica_resident_ratio(self):
        replica_resident_ratio = 100
        if self.d_stats.has_key('ep_num_non_resident') and self.d_stats.has_key('curr_items_tot')\
           and self.d_stats['curr_items_tot'] > 0 and self.d_stats.has_key("curr_items") and self.d_stats.has_key('ep_num_active_non_resident'):
            if self.d_stats['curr_items_tot'] > self.d_stats['curr_items']:
                replica_resident_ratio = 100 - float(self.d_stats['ep_num_non_resident'] - self.d_stats['ep_num_active_non_resident']) / float(self.d_stats['curr_items_tot'] - self.d_stats['curr_items']) * 100
                print replica_resident_ratio
            if replica_resident_ratio < 0:
                replica_resident_ratio = 0
        return "%s=%s%s " % ('replica_resident_ratio', replica_resident_ratio, '%')

if __name__ == "__main__":
    stat = MembaseStats()
    stat.main()

