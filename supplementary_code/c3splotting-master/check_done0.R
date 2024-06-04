

config<-config::get(file = "./config_level0.yml")

patt.want<-"^[0-9]{3}-[0-9]{3}$"
dirs<-c(list.files(config$release4_path,patt=patt.want,full.names=T),list.files(config$release5_path,patt=patt.want,full.names=T))

check.dir<-config$output_path_pdf

icount<-0
icount2<-0

for ( dir in dirs ) {
  if(grepl("release_5.0",dir)) {
    check.dir<-paste0(config$output_path_pdf,"R5/")
  } else {
    check.dir<-paste0(config$output_path_pdf,"R4/")
  }
  dck.want<-substr(basename(dir),5,7)
  sid.want<-substr(basename(dir),1,3)
  fn<-paste0(check.dir,"C3S_D311_Lot1_Marine_sid",sid.want,"_dck",dck.want,".pdf")

  #fn<-gsub("-","_",fn)
  if (file.exists(fn)) {
    #cat("got",fn,"\n")
    icount<-icount+1
  } else {
    cat("missing",fn,"\n")
    icount2<-icount2+1
  }
}
cat("# done",icount,"\n")
cat("# not done",icount2,"\n")
