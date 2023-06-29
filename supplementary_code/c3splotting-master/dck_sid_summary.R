
dck_sid_summary <- function(df,sid_txt_file="sid_list.txt",dck_txt_file="dck_list.txt",inv.ver="2") {

  if ( !("longitude" %in% names(df) ) ) df$longitude<-df$lon
  if ( !("latitude" %in% names(df) ) ) df$latitude<-df$lat
  if ( !("AT_observation_value" %in% names(df) ) ) df$AT_observation_value<-df$at
  if ( !("DPT_observation_value" %in% names(df) ) ) df$DPT_observation_value<-df$dpt
  if ( !("WS_observation_value" %in% names(df) ) ) df$WS_observation_value<-df$w
  if ( !("WD_observation_value" %in% names(df) ) ) df$WD_observation_value<-df$d
  if ( !("SLP_observation_value" %in% names(df) ) ) df$SLP_observation_value<-df$slp
  if ( !("SST_observation_value" %in% names(df) ) ) df$SST_observation_value<-df$sst
  if ( !("report_timestamp" %in% names(df) ) ) df$report_timestamp<-df$date

  sid.want<-df$sid[1]
  dck.want<-df$dck[1]

  sid_txt<-read.delim('sid_list.txt',sep = "\t",header=FALSE)
  sid_txt.want<-sid_txt[sid_txt[,1]==as.numeric(sid.want),2]
  dck_txt<-read.delim('dck_list.txt',sep = "\t",header=FALSE)
  dck_txt.want<-dck_txt[dck_txt[,1]==as.numeric(dck.want),2]

  op<-data.frame(ver=inv.ver,sid=sid.want,sid_txt=sid_txt.want,dck=dck.want,dck_txt=dck_txt.want)
  op$lon_min<-min(df$lon)
  op$lon_max<-max(df$lon)
  op$lat_min<-min(df$lon)
  op$lat_max<-max(df$lon)

  op$bbox<-paste0("POLYGON((",op$lon_min," ",op$lat_min,",",op$lon_min," ",op$lat_max,",",op$lon_max," ",op$lat_max,",",op$lon_max," ",op$lon_min,",",op$lon_min," ",op$lat_min,"))")

  op$dmin<-format(min(df$report_timestamp),"%Y-%m-%d %H-%M-%S")
  op$dmax<-format(max(df$report_timestamp),"%Y-%m-%d %H-%M-%S")

  op$num_at<-sum(!is.na(df$AT_observation_value))
  op$num_wbt<-sum(!is.na(df$DPT_observation_value))
  op$num_ws<-sum(!is.na(df$WS_observation_value))
  op$num_wd<-sum(!is.na(df$WD_observation_value))
  op$num_slp<-sum(!is.na(df$SLP_observation_value))
  op$num_sst<-sum(!is.na(df$SST_observation_value))
  op$num_obs<-nrow(df)
  op$num_rej<-sum(!is.na(df$report_timestamp))

  op$inv_date<-as.character(Sys.Date())
  op$subset<-"total"
  op$p_status<-"inventoried"

  return(op)

}
