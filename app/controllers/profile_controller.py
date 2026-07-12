"""HTTP handlers for profile details and private profile images."""

from flask import Response, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.forms.profile import ProfileForm
from app.repositories import user_repository
from app.utils import profile_images
from utils.audit import log_audit


@login_required
def edit():
    form = ProfileForm(obj=current_user)
    if not form.validate_on_submit():
        return render_template("profile/edit.html", form=form)

    email = form.email.data.strip().lower()
    if user_repository.email_in_use(email, exclude_user_id=current_user.id):
        flash("That email is already used by another account.", "danger")
        return render_template("profile/edit.html", form=form)

    image = None
    if form.profile_image.data and form.profile_image.data.filename:
        is_valid, message = profile_images.validate(form.profile_image.data)
        if not is_valid:
            flash(message, "danger")
            return render_template("profile/edit.html", form=form)
        image = profile_images.build_record(form.profile_image.data)

    user_repository.update_profile(
        user_id=current_user.id,
        display_name=form.display_name.data.strip(),
        email=email,
        profile_bio=form.profile_bio.data.strip() if form.profile_bio.data else "",
        image=image,
    )
    log_audit("profile_updated", "User updated profile information")
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile.edit"))


@login_required
def picture(image_hash):
    if image_hash != current_user.profile_image:
        abort(404)
    image = user_repository.find_owned_profile_image(current_user.id, image_hash)
    if not image or not image.image_data:
        abort(404)
    return Response(
        image.image_data,
        mimetype=image.mime_type,
        headers={
            "Content-Length": str(image.byte_size or len(image.image_data)),
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )
