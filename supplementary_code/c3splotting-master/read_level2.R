
lev2 <- function(dck.want,sid.want) {

  # reads in and combines level2 data from copernicus for selected sid and dck

  config<-config::get(file = "./config_level2.yml")

  if(!exists("read_imma_inv", mode = "function")) source("read_imma_inv.R")
  if(!exists("add_date2", mode = "function")) source("inv_plot_func.R")
  if(!exists("inv_plot", mode = "function")) source("inv_plot.R")
  if(!exists("get_id_class_pfile", mode = "function")) source("get_id_class_pfile.R")

  print.mess<-T

  patt.want<-paste0(sid.want,"-",dck.want)
  dirs<-c(list.files(config$release4_path,patt=patt.want,full.names=T),list.files(config$release5_path,patt=patt.want,full.names=T))

    if ( length(dirs) == 0 ) {
      # no data return null
      return()
    } else {

    flist.header<-list.files(dirs,patt="header",full.names=T)
    if(length(flist.header) > 0 ) {
      nn<-basename(flist.header)
      nn<-gsub("header-","",nn)
      nn<-substring(nn,1,7)

      if ( print.mess ) cat("-----",dck.want,sid.want,"# files=",length(flist.header),"\n")

      sp.header<-lapply(flist.header,read.table,sep="|",header=T,quote='"',comment.char="")
      names(sp.header)<-nn

      if ( print.mess ) cat("read in headers .. ")

      sp<-vector(mode="list",length=length(nn))
      names(sp)<-nn

      for ( vv in c("sst","at","slp","dpt","wd","ws") ) {
        if ( print.mess ) cat(vv," ")
        flist<-list.files(dirs,patt=vv,full.names=T)
        nn2<-basename(flist)
        nn2<-gsub(paste0("observations-",vv,"-"),"",nn2)
        nn2<-substring(nn2,1,7)
        sp.tmp<-lapply(flist,read.table,sep="|",header=T,quote='"',comment.char="")
        names(sp.tmp)<-nn2
        if ( vv == "sst" ) {
          sp.sst<-sp.tmp
        } else if ( vv == "at" ) {
          sp.at<-sp.tmp
        } else if ( vv == "slp" ) {
          sp.slp<-sp.tmp
        } else if ( vv == "dpt" ) {
          sp.dpt<-sp.tmp
        } else if ( vv == "wd" ) {
          sp.wd<-sp.tmp
        } else if ( vv == "ws" ) {
          sp.ws<-sp.tmp
        }
      }

      if ( print.mess ) cat("\n")

      vars.want<-c("observation_id","report_id","observation_height_above_station_surface","observation_value","quality_flag","original_units","advanced_qc","advanced_uncertainty")
      df.blank<-data.frame(matrix(NA,nrow=1,ncol=length(vars.want),dimnames=list(NA,vars.want)))

      for ( ifile in names(sp.header) ) {
        df<-sp.header[[ifile]]
        df$dck<-dck.want
        df$sid<-sid.want

        df.sst<-sp.sst[[ifile]][,vars.want]
        if(is.null(df.sst))df.sst<-df.blank
        names(df.sst)<-paste0("SST_",names(df.sst))
        df<-merge(df,df.sst,by.x="report_id",by.y="SST_report_id",all.x=T)
        rm(df.sst)

        df.at<-sp.at[[ifile]][,vars.want]
        if(is.null(df.at))df.at<-df.blank
        names(df.at)<-paste0("AT_",names(df.at))
        df<-merge(df,df.at,by.x="report_id",by.y="AT_report_id",all.x=T)
        rm(df.at)

        df.slp<-sp.slp[[ifile]][,vars.want]
        if(is.null(df.slp))df.slp<-df.blank
        names(df.slp)<-paste0("SLP_",names(df.slp))
        df<-merge(df,df.slp,by.x="report_id",by.y="SLP_report_id",all.x=T)
        rm(df.slp)

        df.dpt<-sp.dpt[[ifile]][,vars.want]
        if(is.null(df.dpt))df.dpt<-df.blank
        names(df.dpt)<-paste0("DPT_",names(df.dpt))
        df<-merge(df,df.dpt,by.x="report_id",by.y="DPT_report_id",all.x=T)
        rm(df.dpt)

        df.ws<-sp.ws[[ifile]][,vars.want]
        if(is.null(df.ws))df.ws<-df.blank
        names(df.ws)<-paste0("WS_",names(df.ws))
        df<-merge(df,df.ws,by.x="report_id",by.y="WS_report_id",all.x=T)
        rm(df.ws)

        df.wd<-sp.wd[[ifile]][,vars.want]
        if(is.null(df.wd))df.wd<-df.blank
        names(df.wd)<-paste0("WD_",names(df.wd))
        df<-merge(df,df.wd,by.x="report_id",by.y="WD_report_id",all.x=T)
        rm(df.wd)

        sp[[ifile]]<-df
        rm(df)

      }

      if ( print.mess ) cat("read in, about to combine \n")

      df<-do.call(rbind,sp)
      tmp<-ifelse(nchar(df$report_timestamp)==4,NA,df$report_timestamp)
      df$yr<-as.numeric(substr(tmp,1,4))
      df$mo<-as.numeric(substr(tmp,6,7))
      df$dy<-as.numeric(substr(tmp,9,10))
      df$hr<-as.numeric(substr(tmp,12,13))
      df$min<-as.numeric(substr(tmp,15,16))
      df$sec<-as.numeric(substr(tmp,18,19))
      df$hr<-df$hr+df$min/60+df$sec/60/60
      df$min<-NULL
      df$sec<-NULL
      rm(tmp)
      df<-add_date2(df)
      df<-df[!is.na(df$date),]
      df$report_timestamp<-as.POSIXct(df$report_timestamp)

      if ( print.mess ) cat("calculated date variables \n")

      df$pt<-ifelse(df$platform_type==2,5,NA)
      df$pt<-ifelse(df$platform_type==3,15,df$pt)  # rig
      df$pt<-ifelse(df$platform_type==4,6,df$pt)   # moored buoy
      df$pt<-ifelse(df$platform_type==5,7,df$pt)   # drifting buoy
      df$pt<-ifelse(df$platform_type==6,8,df$pt)   # ice buoy
      df$pt<-ifelse(df$platform_type==32,9,df$pt)   # ice station
      df$pt<-ifelse(df$platform_type==33,4,df$pt)   # lightship
      df$pt<-ifelse(is.na(df$platform_type),-1,df$pt)   # other
      df$id<-df$primary_station_id
      df$id<-ifelse(df$id=="null",NA,df$id)
      df$id<-ifelse(nchar(df$id)==0,NA,df$id)
      df$id<-ifelse(df$id=="",NA,df$id)

      if ( print.mess ) cat("wrangled platform types \n")

      # need to remove trailing _gN for this to work
      # add _g so split works if absent
      # also some post-processing fixes in get_id_class_pfile
      tmp.id<-strsplit(paste0(df$id,"_g"),"_g")
      tmp.id<-sapply(tmp.id,function(X) X[[1]])
      tmp.id<-ifelse(tmp.id =="null",NA,tmp.id)
      tmp.id<-ifelse(tmp.id =="NA",NA,tmp.id)

      # config files to define id types for different dck
      if ( max(df$yr,na.rm=T) <= 2014 ) {
       pfile<-paste0(config$json_files_path4,"/dck", dck.want, ".json")
      } else {
       pfile<-paste0(config$json_files_path5,"/dck", dck.want, ".json")
      }
      df$id.class<-get_id_class_pfile(dck.want,tmp.id,pfile=pfile)
      df$id.class<-ifelse(df$dck %in% c(700,993) & grepl("^[0-9]{5}$",df$id), "5digit_buoy_number",df$id.class)
      df$id.class<-ifelse(df$dck %in% c(926,994) & grepl("^[0-9]{7}$",df$id), "7digit_buoy_number",df$id.class)
      df$id.class<-ifelse(df$dck %in% c(994,995) & grepl("^[A-Z]{4}[0-9]{1}$",df$id), "CMAN",df$id.class)


      if ( print.mess ) cat("done \n")
    }  # end check for files in dir
  } # check for missing dir
   return(df)
} # end function
