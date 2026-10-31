// Exact pointer-cell selection is independent of the cursor's visual spring.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/pixel_workshop.hpp"
#include <array>
#include <cassert>
#include <cstdio>
#include <limits>
int main(){
 museum::PixelWorkshop picture;hui::ui::Feedback feedback;
 std::array<unsigned,64> original{};
 for(unsigned y=0;y<8;++y)for(unsigned x=0;x<8;++x)original[y*8+x]=picture.shade(x,y);
 picture.set_cursor(7,7); // same frame as a first contact at the far corner
 hui::InputFrame click;click.connected=true;click.pressed=hui::action_bit(hui::Action::confirm);
 picture.handle(click,feedback);
 assert(picture.cursor_x()==7&&picture.cursor_y()==7);
 for(unsigned y=0;y<8;++y)for(unsigned x=0;x<8;++x)
  assert(picture.shade(x,y)==(x==7&&y==7?(original[63]+1)%4:original[y*8+x]));
 picture.set_cursor(std::numeric_limits<unsigned>::max(),9);
 assert(picture.cursor_x()==7&&picture.cursor_y()==7);
 picture.set_cursor(0,0);picture.handle(click,feedback);
 assert(picture.cursor_x()==0&&picture.cursor_y()==0&&picture.shade(0,0)==(original[0]+1)%4);
 picture.update(1.f/120);assert(picture.cursor_x()==0&&picture.cursor_y()==0);
 const auto shade=picture.shade(0,0);click.focus_lost=true;picture.handle(click,feedback);assert(picture.shade(0,0)==shade);
 std::puts("PASS pixel pointer: far-cell contact+click changes exactly that cell; bounds clamp; navigation/animation preserve exact cell; intercepted click ignored");
}
