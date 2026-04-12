from uploadthing.routers import FileRouter
from uploadthing.types import FileResponse

class WeddingPhotoRouter(FileRouter):
    wedding_photos = (
        FileRouter.FileRoute(
            name="wedding_photos",
            path="wedding-photos",
            maxFileSize="16MB",
            maxFileCount=10,
        )
        .middleware(lambda req: req)
        .on_upload_complete(lambda data: FileResponse())
    )
