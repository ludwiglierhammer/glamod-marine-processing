my_args = commandArgs(trailingOnly=TRUE)

if (length(my_args) == 0) my_args<-my_args2

start.dck<-as.numeric(my_args[1])
if(length(my_args) == 2 ) {
  end.dck<-as.numeric(my_args[2])
} else {
  end.dck<-start.dck+99
}

if(!exists("lev0", mode = "function")) source("read_ds_imma.R")
if(!exists("dck_sid_summary", mode = "function")) source("dck_sid_summary.R")

# config file sets input and output directories
config<-config::get(file = "./config_level0.yml")

for ( dck.want in as.character(seq(start.dck,end.dck,1)) ) {
  cat("checking dck", dck.want, "\n")
  for ( sid in as.character(seq(1,299,1)) ) {
    sid.want<-paste0("00",sid)
    sid.want<-substring(sid.want,nchar(sid.want)-2,nchar(sid.want))
    # old release
    release.want<-4
    df.lev0<-lev0(dck.want,sid.want,release.want)
    if ( !is.null(df.lev0) ) {
      odir<-paste0(config$output_path_pdf,'R4/')
      if ( !dir.exists(odir)) dir.create(odir, recursive=TRUE)
      pdfname<-paste0(odir,'C3S_D311_Lot1_Marine_sid',sid.want,'_dck',dck.want,'.pdf')
      p<-inv_plot(level=0,df.lev0,dck.want,sid.want,dev="pdf",pdfname = pdfname )
      odir<-paste0(config$output_path_txt,'R4/')
      if ( !dir.exists(odir)) dir.create(odir, recursive=TRUE)
      op<-dck_sid_summary(df.lev0,sid_txt_file="sid_list.txt",dck_txt_file="dck_list.txt",inv.ver="2")
      write.table(op,paste0(odir,dck.want,"_",sid.want,".txt"),sep=",",col.names=T)
    }
    # new release
    release.want<-5
    df.lev0<-lev0(dck.want,sid.want,release.want)
    if ( !is.null(df.lev0) ) {
      odir<-paste0(config$output_path_pdf,'R5/')
      if ( !dir.exists(odir)) dir.create(odir, recursive=TRUE)
      pdfname<-paste0(odir,'C3S_D311_Lot1_Marine_sid',sid.want,'_dck',dck.want,'.pdf')
      p<-inv_plot(level=0,df.lev0,dck.want,sid.want,dev="pdf",pdfname = pdfname )
      odir<-paste0(config$output_path_txt,'R5/')
      if ( !dir.exists(odir)) dir.create(odir, recursive=TRUE)
      op<-dck_sid_summary(df.lev0,sid_txt_file="sid_list.txt",dck_txt_file="dck_list.txt",inv.ver="2")
      write.table(op,paste0(odir,dck.want,"_",sid.want,".txt"),sep=",",col.names=T)
    }
  }
}
